node('linux')
{
  stage('Build') {
    build job: 'Port-Pipeline', parameters: [string(name: 'PORT_GITHUB_REPO', value: 'https://github.com/ZOSOpenTools/pinentryport.git'), string(name: 'PORT_DESCRIPTION', value: 'pinentry is a small collection of dialog programs that allow GnuPG to read passphrases and PIN numbers in a secure manner.' )]
  }
}
