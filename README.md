# A simple Program to back up files to Google Drive

Though any files can be backed up, It is created for docker files (docker-compose.yaml) etc.

## Usage
rename `.env.sample` to `.env` and rename the variables accordingly

Note the following:
- for environment variables
  - `FILENAME`: The file name will be appended to the file after the date eg `2011-01-01-MYBACKUP.tar.gz`
  - `ARCHIVE_PATH`: This needs to be absolute path
  - `DOCKER_CONTAINERS`: Containers to stop before archiving, if `all` is set, it will stop all containers and `none` will not stop any containers (recommended if you are not backing docker containers) 
  - `GNUPG_RECIPIENTS`: Which GPG Key to use for encryption
  - `BACKUP_COPIES`: How many recent copies to keep, the rest will be deleted 
  - `DATE_FORMAT`: Date format, uses [Python datetime strftime format](https://strftime.org/)
  - `NTFY_URL` & `NTFY_AUTH` are both optional

- Before running, ensure you have a GPG key, `client.secrets.json` and `credentials.json`, else run `get_gdrive_token.py` to get `credentials.json`
