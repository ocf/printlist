from pathlib import Path

from transpire.resources import Deployment, Ingress, Secret, Service
from transpire.types import Image
from transpire.utils import get_image_tag, get_revision

name = "printlist"
auto_sync = True


def images():
    yield Image(name="printlist", path=Path("/"), registry="ghcr")


def objects():
    yield Secret(
        name="printlist",
        string_data={
            "broker.conf": "",
        },
    ).build()

    dep = Deployment(
        name="printlist",
        image=get_image_tag("printlist"),
        ports=[8000],
    )
    dep.obj.spec.template.spec.dns_policy = "ClusterFirst"
    dep.obj.spec.template.spec.dns_config = {"searches": ["ocf.berkeley.edu"]}

    dep.obj.spec.template.spec.volumes = [
        {"name": "secrets", "secret": {"secretName": "printlist"}},
    ]

    dep.obj.spec.template.spec.containers[0].volume_mounts = [
        {"name": "secrets", "mountPath": "/usr/src/app/conf"},
    ]

    yield dep.build()

    svc = Service(
        name="printlist",
        selector=dep.get_selector(),
        port_on_pod=8000,
        port_on_svc=80,
    )
    yield svc.build()

    ing = Ingress.from_svc(
        svc=svc,
        host="printlist.ocf.berkeley.edu",
        path_prefix="/",
    )
    yield ing.build()
