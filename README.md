# A simple Program to back up files to Google Drive

Though any files can be backed up, It is created to docker files (docker-compose.yaml) etc.
Remove all lines with subprocess if you do not intent to use it for docker files.

## Usage
rename `.env.sample` to `.env` and rename the variables accordingly

Note the following:

- for the environment variables
  - `FILENAME`: The file name will be appended to the file after the date eg `2011-01-01-MYBACKUP.tar.gz`
  - `DOCKER_CONTAINERS`: Containers to stop before archiving, if `all` is set, it will stop all containers and `none` will not stop any containers 
  - `GNUPG_RECIPIENTS`: Which GPG Key to use for encryption
  - `BACKUP_COPIES`: How many copies to keep, will delete the rest 
  - `DATE_FORMAT`: Date format, uses [Python datetime strftime format](https://strftime.org/) 

Before running, ensure you have a GPG key, `client.secrets.json` and `credentials.json`, else run `get_gdrive_token.py` to get `credentials.json`
