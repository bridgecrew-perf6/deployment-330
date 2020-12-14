# How to use deployment project

## Requirements
This projects requires
- Python 3.7+
- Poetry

## Setup

### Mac OS
Usage of the package manager `HomeBrew`:

```
> /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
```

Then (Python):
```
> brew install python
```

Then (Poetry):
```
> pip install poetry
```

### Windows

Usage of the package manager `Chocolatey`: in a powershell terminal with admin rights:

```
> Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
```

Then you need to launch a new powershell still in admin to install python:
```
> choco install python --pre
```

Then again you need to launch a new powershell still in admin to install poetry:
```
> pip install poetry
```

Then to proceed with the rest of the steps, the terminal has again to be restarted.

## Environment variables
### Mac OS / Linux:
```
export OC_PATH=/path/to/oc
export OC_USERNAME=openshift-username
export OC_PASSWORD=openshift-password

export NEXUS_USER=jenkins@devops.azure
export NEXUS_PASSWORD=123456
```

### Windows:
```
SET OC_PATH=C:\path\to\oc.exe
SET OC_USERNAME=openshift-username
SET OC_PASSWORD=openshift-password

SET NEXUS_USER=jenkins@devops.azure
SET NEXUS_PASSWORD=J3nk1ns4zur3

```

## Project set up

Get all required dependencies:

`poetry install`

## Run

### Load the runtime dependencies
`source .venv/bin/activate`

### Execute



```
-> % python3 deployment/oc_deploy.py -h  
 usage: oc_deploy.py [-h] [--namespace NAMESPACE]
                     [--deployment DEPLOYMENT [DEPLOYMENT ...]]
                     [--release RELEASE]
 
 Import and tag latest images on Openshift.
 
 optional arguments:
   -h, --help            show this help message and exit
   --namespace NAMESPACE
                         Namespace where to execute.
   --deployment DEPLOYMENT [DEPLOYMENT ...]
                         Specific deployment config image to tag.
   --release RELEASE     Is release?

```
### Examples
Deploy latest snapshots to TA:

`poetry run python3 deployment/oc_deploy.py --namespace ta --release False`

Deploy latest releases to INT:

`poetry run python3 deployment/oc_deploy.py --namespace int --release True`

Deploy latest content-ds and content-bs to TA:

`poetry run python3 deployment/oc_deploy.py --namespace ta --deployment content-bs-service content-ds-service`