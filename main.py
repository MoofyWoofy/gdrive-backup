from pydrive2.auth import GoogleAuth, RefreshError
from pydrive2.drive import GoogleDrive
from shutil import make_archive
import subprocess
import dotenv
from os import getenv, remove as os_remove_file
import os.path
import gnupg
from datetime import datetime
from sys import stderr
import requests
from base64 import b64encode


def run_docker_commands(command, docker_containers_scoped):
    try:
        # subprocess.run("docker pause $(docker ps -q)", shell=True, check=True)
        subprocess.run(["docker", "container", command] + docker_containers_scoped, check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as err:
        print(err, file=stderr)


def get_file_location(file_path) -> str:
    # returns the location adding the slash / for *nix and \ for Windows
    return os.path.join(os.path.dirname(__file__), file_path)


def humanbytes(B):
    """Return the given bytes as a human friendly KB, MB, GB, or TB string."""
    B = float(B)
    KB = float(1024)
    MB = float(KB ** 2) # 1,048,576
    GB = float(KB ** 3) # 1,073,741,824
    TB = float(KB ** 4) # 1,099,511,627,776

    if B < KB:
        return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
    elif KB <= B < MB:
        return '{0:.2f} KB'.format(B / KB)
    elif MB <= B < GB:
        return '{0:.2f} MB'.format(B / MB)
    elif GB <= B < TB:
        return '{0:.2f} GB'.format(B / GB)
    elif TB <= B:
        return '{0:.2f} TB'.format(B / TB)


def send_ntfy(ntfy: dict, title: str, message: str, tags: str, priority: str):
    requests.post(ntfy["url"],
                  data=message.encode(encoding='utf-8'),
                  headers={
                      "Title": title,
                      "Priority": priority,
                      "Tags": tags,
                      "Authorization": f"Basic {b64encode(ntfy['auth'].encode()).decode()}"
                  })


if __name__ == '__main__':
    dotenv.load_dotenv()

    # Get docker containers
    docker_containers = getenv("DOCKER_CONTAINERS", ["none"]).split(',')
    if len(docker_containers) == 1 and docker_containers[0] == "none":  # Do not run docker commands
        docker_containers = False
    elif len(docker_containers) == 1 and docker_containers[0] == "all":  # Get all docker running containers
        result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], check=True, capture_output=True)
        docker_containers = result.stdout.decode().splitlines()

    date_format = getenv("DATE_FORMAT", "%Y-%m-%d")
    filename = f'{datetime.now().strftime(date_format)}{getenv("FILENAME", "")}'

    # Stop all docker containers
    if docker_containers:
        run_docker_commands("stop", docker_containers)

    # Create archive
    make_archive(filename, 'gztar', getenv("ARCHIVE_PATH"))
    filename += ".tar.gz"

    # Resume docker containers
    if docker_containers:
        run_docker_commands("start", docker_containers)

    # Encrypt Tarball
    gpg = gnupg.GPG()
    with open(get_file_location(filename), 'rb') as file:
        status = gpg.encrypt_file(
            file, getenv("GNUPG_RECIPIENTS").split(","),
            passphrase=getenv("GNUPG_PASSPHRASE"), output=f"{get_file_location(filename)}.gpg")

    try:
        # Connect to Google Drive
        gauth = GoogleAuth()
        drive = GoogleDrive(gauth)

        # Upload to Google Drive
        file = drive.CreateFile({'parents': [{'id': getenv("GOOGLE_DRIVE_FOLDER_ID")}]})
        file.SetContentFile(f"{get_file_location(filename)}.gpg")
        file.Upload()
        del file

        # Keep only latest 3 files - https://developers.google.com/drive/api/guides/search-files
        file_list = drive.ListFile({'q': f"'{getenv('GOOGLE_DRIVE_FOLDER_ID')}' in parents and trashed=false"}).GetList()

        file_list.sort(key=lambda x: datetime.strptime(x['title'], f'{date_format}{getenv("FILENAME", "")}.tar.gz.gpg'))

        for i in range(0, len(file_list) - int(getenv("BACKUP_COPIES"))):
            file_list[i].Delete()

        # Send notification, backup success
        if getenv("NTFY_URL") and getenv("NTFY_AUTH"):
            send_ntfy(
                {"url": getenv("NTFY_URL"), "auth": getenv("NTFY_AUTH")},
                "Backup Successful",
                f"{humanbytes(os.path.getsize(get_file_location(filename)+'.gpg'))} Uploaded!",
                "heavy_check_mark",
                "low"
            )

    except RefreshError as err:
        print(err, file=stderr)
        # Send notification, Backup failed
        if getenv("NTFY_URL") and getenv("NTFY_AUTH"):
            send_ntfy(
                {"url": getenv("NTFY_URL"), "auth": getenv("NTFY_AUTH")},
                "Backup Failed",
                f"{err}",
                "x",
                "high"
            )
    finally:
        # Remove local files
        os_remove_file(filename)
        os_remove_file(f"{filename}.gpg")
