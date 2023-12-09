from pydrive2.auth import GoogleAuth, RefreshError
from pydrive2.drive import GoogleDrive
from shutil import make_archive
import subprocess
import dotenv
from os import getenv, remove as os_remove_file
import gnupg
from datetime import datetime
from sys import stderr


def run_docker_commands(command, docker_containers_scoped):
    try:
        # subprocess.run("docker pause $(docker ps -q)", shell=True, check=True)
        subprocess.run(["docker", "container", command] + docker_containers_scoped, check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as err:
        print(err, file=stderr)


def send_ntfy():
    pass


if __name__ == '__main__':
    dotenv.load_dotenv()

    # Get docker containers
    docker_containers = getenv("DOCKER_CONTAINERS", "none").split(',')
    if docker_containers == "none":  # Do not run docker commands
        docker_containers = False
    elif docker_containers == "all":  # Get all docker running containers
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
    with open(filename, 'rb') as file:
        status = gpg.encrypt_file(file, getenv("GNUPG_RECIPIENTS").split(","), passphrase=getenv("GNUPG_PASSPHRASE"), output=f"{filename}.gpg")

    try:
        # Connect to Google Drive
        gauth = GoogleAuth()
        drive = GoogleDrive(gauth)

        # Upload to Google Drive
        file = drive.CreateFile({'parents': [{'id': getenv("GOOGLE_DRIVE_FOLDER_ID")}]})
        file.SetContentFile(f"{filename}.gpg")
        file.Upload()
        del file

        # Keep only latest 3 files - https://developers.google.com/drive/api/guides/search-files
        file_list = drive.ListFile({'q': f"'{getenv('GOOGLE_DRIVE_FOLDER_ID')}' in parents and trashed=false"}).GetList()

        file_list.sort(key=lambda x: datetime.strptime(x['title'], f'{date_format}{getenv("FILENAME", "")}.tar.gz.gpg'))

        for i in range(0, len(file_list) - int(getenv("BACKUP_COPIES"))):
            file_list[i].Delete()

        send_ntfy()  # Send notification NTFY, backup success
    except RefreshError as err:
        print(err, file=stderr)
        send_ntfy()  # Notify Backup failed
    finally:
        # Remove local files
        os_remove_file(filename)
        os_remove_file(f"{filename}.gpg")
