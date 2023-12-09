from pydrive2.auth import GoogleAuth


if __name__ == '__main__':
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.
    # auth_url = gauth.GetAuthUrl();print(auth_url)  # Create authentication url user needs to visit
