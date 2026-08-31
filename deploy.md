# Deploying BlueOS Extensions

This document describes how to build, test on target hardware (Raspberry Pi), and deploy _Surftrak Fixit_ as a BlueOS extension.

---

## Prerequisites

- **Docker** with **Buildx** plugin installed.
- **Docker Hub** account with write access.
- **Git** repository access.

---

## 1. One-Time Buildx & QEMU Setup

BlueOS runs on both x86 (development machines) and ARM architectures (Raspberry Pi 3/4/5 running 32-bit `linux/arm/v7` or 64-bit `linux/arm64`). Docker Buildx with QEMU enables building multi-architecture container images on your x86 host machine.

```bash
# Create and activate a multi-architecture builder
docker buildx create --name multiarch --driver docker-container --use
docker buildx inspect --bootstrap

# Register QEMU multi-arch emulation handlers
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

---

## 2. Release Preparation Checklist

Before building a release:

1. **Update version in `Dockerfile`**:
   Ensure `LABEL version="vX.Y.Z"` matches your target version.
2. **Update version in `app/static/register_service`**:
   Ensure `"version": "vX.Y.Z"` matches.
3. **Update `README.md`**:
   Add notes under `## Releases` detailing the changes.
4. **Commit the changes**:
   ```bash
   git add Dockerfile app/static/register_service README.md
   git commit -m "Bump version to vX.Y.Z"
   ```

---

## 3. Build and Push Multi-Architecture Image

Log in to Docker Hub and build for `linux/amd64`, `linux/arm/v7`, and `linux/arm64`:

```bash
# Log in to Docker Hub
docker login

# Build and push tagged image
docker buildx build \
  --platform linux/amd64,linux/arm/v7,linux/arm64 \
  -t clydemcqueen/surftrak_fixit:v1.0.0-beta.3 \
  --push .

# (Optional) Update latest tag
docker buildx build \
  --platform linux/amd64,linux/arm/v7,linux/arm64 \
  -t clydemcqueen/surftrak_fixit:latest \
  --push .
```

---

## 4. Testing on Raspberry Pi with BlueOS (Pre-Release)

To test changes on your Raspberry Pi running BlueOS before making an official public release:

### Tagging Strategy for Testing
> [!TIP]
> The [BlueOS Extensions Repository](https://github.com/bluerobotics/BlueOS-Extensions-Repository) automatically monitors Docker Hub for valid **SemVer** tags (e.g., `v1.1.0-beta.1`). To prevent unfinished builds from appearing in the public store, use a test tag (such as `v1.1.0-beta.1-dev`) when building for testing.

1. **Build and push the multi-arch test image**:
   ```bash
   docker buildx build --platform linux/amd64,linux/arm/v7,linux/arm64 -t clydemcqueen/surftrak_fixit:v1.1.0-beta.1-dev --push .
   ```
2. **Open BlueOS in your browser**: Navigate to `http://192.168.2.2` (or `http://blueos.local`).
3. **Enable Pirate Mode (Developer Mode)**:
   - Click the settings/user profile icon in the top-right header / sidebar.
   - Enable **Pirate Mode**.
4. **Install / Load Custom Extension**:
   - Go to **Extensions** in the sidebar -> **Installed** tab.
   - Click the **+** button in the lower right.
   - Enter the extension details:
     - **Identifier**: `clydemcqueen.surftrak_fixit`
     - **Name**: `surftrak_fixit`
     - **Docker Image**: `clydemcqueen/surftrak_fixit`
     - **Docker Tag**: `v1.1.0-beta.1-dev`
     - **Settings**:
       ```json
       {
         "ExposedPorts": {
           "8080/tcp": {}
         },
         "HostConfig": {
           "ExtraHosts": ["host.docker.internal:host-gateway"],
           "PortBindings": {
             "8080/tcp": [
               {
                 "HostPort": ""
               }
             ]
           }
         },
         "Env": ["MAVLINK2REST_URL=http://host.docker.internal/mavlink2rest/v1"]
       }
       ```
   - Click **Create**.
5. **Verify Extension**:
   - BlueOS will pull the ARM image from Docker Hub and start the container on the Pi.
   - Click on **Surftrak Fixit** in the BlueOS sidebar menu to verify the UI and ArduSub SITL communication.
   - Check container status and logs under **Extensions** -> **Installed**.

---

## 5. Official Release & Publishing

Once testing is complete and the extension is ready for public release:

### A. Git Tagging
Commit any final changes, create the official release tag, and push to GitHub:
```bash
git tag -a v1.0.0-beta.3 -m "Release v1.0.0-beta.3"
git push origin v1.0.0-beta.3
```

### B. Build and Push Official Docker Tag
Build and push the multi-architecture image with the official SemVer tag:
```bash
docker buildx build \
  --platform linux/amd64,linux/arm/v7,linux/arm64 \
  -t clydemcqueen/surftrak_fixit:v1.0.0-beta.3 \
  --push .

# (Optional) Update latest tag
docker buildx build \
  --platform linux/amd64,linux/arm/v7,linux/arm64 \
  -t clydemcqueen/surftrak_fixit:latest \
  --push .
```

### C. BlueOS Store Update
How the extension appears in the BlueOS store:
- **Existing Registered Extensions**: Because `surftrak_fixit` is already registered in [BlueOS-Extensions-Repository](https://github.com/bluerobotics/BlueOS-Extensions-Repository), **no new Pull Request is needed**. The repository's GitHub Action regularly queries the Docker Hub API, detects the new SemVer tag (`v1.0.0-beta.3`), extracts the Docker labels, and updates the public `manifest.json`.
- **New Extensions Only**: If registering a brand new extension for the first time, a PR is required with the extension's `metadata.json` and icon.

---

## References

- [BlueOS Extension Development Guide](https://blueos.cloud/docs/blueos/1.2/development/extensions/)
- [BlueOS Example Extensions](https://github.com/bluerobotics/BlueOS-examples)
- [BlueOS Extensions Registry Repository](https://github.com/bluerobotics/BlueOS-Extensions-Repository)
- [WL UGPS Extension Reference](https://github.com/clydemcqueen/wl_ugps_external_extension/)
