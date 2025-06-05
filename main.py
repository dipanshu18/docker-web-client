import docker
import docker.errors
from flask import Flask, flash, redirect, render_template, request

app = Flask(__name__)
app.secret_key = "superSecEret@123#$"

client = docker.from_env()


@app.route("/")
def home():
    images = client.images.list()
    image_data = []
    for image in images:
        tags = image.tags[0] if image.tags else "<none>:<none>"
        size_mb = image.attrs["Size"] / (1024 * 1024)  # Size in MB
        image_data.append({"tag": tags, "size_mb": round(size_mb, 2)})

    running_containers = client.containers.list()
    running_containers_data = []

    for container in running_containers:
        ports = container.attrs["NetworkSettings"]["Ports"]
        running_containers_data.append(
            {
                "id": container.id,
                "image": (
                    container.image.tags[0] if container.image.tags else "<none>:<none>"
                ),
                "name": container.name,
                "ports": ports,
            }
        )

    all_containers = client.containers.list(all=True)
    all_containers_data = []
    for container in all_containers:
        ports = container.attrs["NetworkSettings"]["Ports"]
        all_containers_data.append(
            {
                "id": container.id,
                "image": (
                    container.image.tags[0] if container.image.tags else "<none>:<none>"
                ),
                "name": container.name,
                "status": container.status,
                "ports": ports,
            }
        )

    return render_template(
        "index.html",
        images=image_data,
        running_containers=running_containers_data,
        all_containers=all_containers_data,
    )


@app.route("/container", methods=["POST"])
def container_actions():
    action = request.args.get("action")
    container_name = request.form["name"]
    container = client.containers.get(container_name)

    if action == "stop":
        container.stop()
        flash(
            f"Container id:'{container.id}', image:'{container.image.tags[0]}', name:'{container_name}' stopped successfully.",  # type: ignore
            "success",
        )
    elif action == "start":
        container.start()
        flash(
            f"Container id:'{container.id}', image:'{container.image.tags[0]}', name:'{container_name}' started successfully.",  # type: ignore
            "success",
        )

    return redirect("/")


@app.route("/image", methods=["POST", "DELETE"])
def image_actions():
    method_override = request.form["_method"]
    image_name = request.form["name"]

    if method_override == "DELETE":
        try:
            image = client.images.get(image_name)
            image.remove()
            flash(f"Image '{image_name}' removed successfully.", "success")
        except docker.errors.APIError as e:
            error_msg = str(e.explanation)
            flash(f"Error removing image '{image_name}': {error_msg}", "danger")
        return redirect("/")

    # Pull image
    try:
        if ":" in image_name:
            repo, tag = image_name.split(":", 1)
            client.images.pull(repo, tag)
        else:
            client.images.pull(image_name)
        flash(f"Image '{image_name}' pulled successfully.", "success")
    except docker.errors.APIError as e:
        flash(f"Error pulling image '{image_name}': {str(e.explanation)}", "danger")

    return redirect("/")
