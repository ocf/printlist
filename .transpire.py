from yaml import safe_load
from pathlib import Path

from transpire.resources import Deployment, Ingress, Service, Secret
from transpire.internal import surgery
from transpire.types import Image
from transpire.utils import get_image_tag

name = "printlist"


def objects():
    dep = Deployment(
        name="printlist",
        image=get_image_tag("printlist"),
        ports=[8000],
    )

    svc = Service(
        name="printlist",
        selector=dep.get_selector(),
        port_on_pod=8000,
        port_on_svc=80,
    )

    ing = Ingress.from_svc(
        svc=svc,
        host="printlist.ocf.berkeley.edu",
        path_prefix="/",
    )

    string_data = {
        "stringData": {
            "broker.conf": "[broker]\nhost = broker.ocf.berkeley.edu\npassword = <%= redis_pw %>"
        }
    }

    sec = Secret(name="broker-conf", string_data=string_data)

    volume_mounts = {
        "volumeMounts": [{"name": "conf", "mountPath": "/usr/src/app/conf"}]
    }

    volumes = {"volumes": [{"name": "conf", "secret": {"secretName": "broker-conf"}}]}

    dep = dep.build()
    dep = surgery.shelve(
        dep, ["spec", "template", "spec", "containers", 0], volume_mounts, create_parents=True
    )
    dep = surgery.shelve(dep, ["spec", "template", "spec"], volumes, create_parents=True)

    yield dep
    yield svc.build()
    yield ing.build()
    yield sec.build()


def images():
    yield Image(name=name, path=Path("/"))
