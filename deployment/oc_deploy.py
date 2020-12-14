import argparse
import json
import os
import requests
import subprocess
from enum import Enum
from requests.auth import HTTPBasicAuth

OC_PATH = os.getenv('OC_PATH')
OC_USERNAME = os.getenv('OC_USERNAME')
OC_PASSWORD = os.getenv('OC_PASSWORD')

NEXUS_USER = os.getenv('NEXUS_USER')
NEXUS_PASSWORD = os.getenv('NEXUS_PASSWORD')
BASIC_AUTH = HTTPBasicAuth(NEXUS_USER, NEXUS_PASSWORD)

DOCKER_REPOSITORY = "devops.digital.belgium.be:1443"

class Service:
    def __init__(self, name: str, is_ta_only=False, prefix="hcp-", is_snapshot_only=False):
        self.name = name
        self.is_ta_only = is_ta_only
        self.prefix = prefix
        self.is_snapshot_only = is_snapshot_only


class ServiceEnum(Enum):
    AUDIT_BS = Service(name="audit-bs-service")
    AUDIT_DS = Service(name="audit-ds-service")
    CONTENT_BS = Service(name="content-bs-service")
    CONTENT_DS = Service(name="content-ds-service")
    FEDERATED_16 = Service(name="federated-bs-service-1.6")
    FEDERATED_21 = Service(name="federated-bs-service-2.1")
    FEDERATED_22 = Service(name="federated-bs-service-2.2")
    FEDERATED_22_Enterprise = Service(name="federated-bs-service-2.2-enterprise")
    REPORTING_BS = Service(name="reporting-bs-service")
    REPORTING_DS = Service(name="reporting-ds-service")
    JWK_SIMULATOR = Service(name="jwk-simulator", is_ta_only=True, prefix="", is_snapshot_only=True)


def get_latest_snapshot(service: ServiceEnum):
    response = requests.get(
        f"https://devops.digital.belgium.be/nexus/service/rest/v1/search?repository=docker-ecosystem&name={service.value.prefix}{service.value.name}&sort=version&version=*SNAPSHOT*",
        auth=BASIC_AUTH)
    print(response.text)
    return json.loads(response.text)["items"][0]["version"]


def get_latest_release(service: ServiceEnum):
    response = requests.get(
        f"https://devops.digital.belgium.be/nexus/service/rest/v1/search?repository=docker-ecosystem&name=hcp-{service.value.name}&sort=version",
        auth=BASIC_AUTH)
    response_body = json.loads(response.text)
    items = response_body['items']
    return next(filter(lambda item: "SNAPSHOT" not in item['version'], items))["version"]


def get_version(is_release: bool, service: ServiceEnum):
    if is_release or service == ServiceEnum.JWK_SIMULATOR:
        return get_latest_release(service)
    else:
        return get_latest_snapshot(service)


class Namespace(Enum):
    TA = "bosa-dt-test-hcp-fedapi"
    INT = "bosa-dt-acc-hcp-fedapi"
    PROD = "bosa-dt-prod-hcp-fedapi"


def main():
    arguments = parse_arguments()
    print(arguments)
    namespace: Namespace = {
        "prod": Namespace.PROD,
        "int": Namespace.INT,
        "ta": Namespace.TA
    }.get(arguments.namespace, Namespace.TA)

    login()

    if arguments.deployment:
        tag_and_import_specific(deployments=arguments.deployment, namespace=namespace,
                                is_release=arguments.release == "True", offline=arguments.offline == "True")
    else:
        tag_and_import_all(namespace=namespace, is_release=arguments.release == "True", offline=arguments.offline == "True")

def is_deployable(namespace: Namespace, is_release: bool, service: ServiceEnum):
    if namespace is not Namespace.TA:
        if service.value.is_ta_only:
            return False
    elif is_release and service.value.is_snapshot_only:
        return False
    return True


def tag_and_import_specific(deployments: list, namespace: Namespace, is_release: bool, offline: bool):
    for service in ServiceEnum:
        for deployment in deployments:
            if deployment in service.value.name and is_deployable(namespace=namespace, is_release=is_release, service=service):
                tag_and_import_service(is_release, namespace, service, offline=offline)


def tag_and_import_all(namespace: Namespace, is_release: bool, offline: bool):
    for service in ServiceEnum:
        if is_deployable(namespace=namespace, is_release=is_release, service=service) :
                tag_and_import_service(is_release, namespace, service, offline=offline)


def tag_and_import_service(is_release, namespace, service, offline: bool):
    version = get_version(is_release=is_release, service=service)
    import_image(service=service, namespace=namespace, version=version, offline=offline)
    tag(service=service, namespace=namespace, version=version, offline=offline)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Import and tag latest images on Openshift.')
    parser.add_argument('--namespace', dest='namespace', help='Namespace where to execute.')
    parser.add_argument("--deployment", dest='deployment', help='Specific deployment config image to tag.', nargs='+')
    parser.add_argument("--release", dest='release', help='Is release?')
    parser.add_argument("--offline", dest='offline', help='Disables the actual execution of the oc commands')
    return parser.parse_args()


def login():
    out = subprocess.Popen([OC_PATH, 'login', '-u', OC_USERNAME, '-p', OC_PASSWORD],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out.communicate()


def import_image(namespace: Namespace, service: ServiceEnum, version: str, offline: bool):
    print(
        f"oc import-image {service.value.prefix}{service.value.name}:{version} --from {DOCKER_REPOSITORY}/{service.value.prefix}{service.value.name}:{version} --confirm -n {namespace.value}")
    execute_command([OC_PATH, 'import-image', f'{service.value.prefix}{service.value.name}:{version}',
         f'--from={DOCKER_REPOSITORY}/{service.value.prefix}{service.value.name}:{version}',
         '--confirm', '-n', namespace.value], offline=offline)


def tag(namespace: Namespace, service: ServiceEnum, version: str, offline:bool):
    print(
        f"oc tag --source=docker {DOCKER_REPOSITORY}/{service.value.prefix}{service.value.name}:{version} {service.value.prefix}{service.value.name}:latest -n {namespace.value}")
    execute_command(
        [OC_PATH, 'tag', '--source=docker',
         f"{DOCKER_REPOSITORY}/{service.value.prefix}{service.value.name}:{version}",
         f"{service.value.prefix}{service.value.name}:latest", "-n", namespace.value], offline=offline)

def execute_command(command_to_execute, offline: bool):
    if not offline:
        out = subprocess.Popen(command_to_execute)
        out.communicate()

if __name__ == '__main__':
    main()
