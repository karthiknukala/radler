# Radler Builder Image
# This image provides a complete build environment for compiling .radl files
# into ROS2 packages and optionally generating per-node Docker containers.
#
# Usage:
#   docker run -v $(pwd):/project -v /tmp/output:/output radler/builder \
#       /project/my_system.radl --plant plant
#
# With Docker output:
#   docker run -v $(pwd):/project -v /tmp/output:/output radler/builder \
#       /project/my_system.radl --plant plant --docker

ARG FROM_IMAGE=ubuntu:noble
FROM $FROM_IMAGE

# Setup timezone
RUN echo 'Etc/UTC' > /etc/timezone && \
    ln -s /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    apt-get update && apt-get install -q -y tzdata && rm -rf /var/lib/apt/lists/*

# Install packages
RUN apt-get update && apt-get install -q -y \
    bash-completion \
    dirmngr \
    gnupg2 \
    lsb-release \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Setup ROS2 keys
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654

# Setup sources.list
RUN echo "deb http://packages.ros.org/ros2/ubuntu `lsb_release -sc` main" > /etc/apt/sources.list.d/ros2-latest.list

# Setup environment
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install bootstrap tools
RUN apt-get update && apt-get install --no-install-recommends -y \
    git \
    python3-rosdep \
    python3-vcstool \
    && rm -rf /var/lib/apt/lists/*

# Install python packages for colcon
RUN pip3 install --break-system-packages -U \
    argcomplete \
    colcon-common-extensions \
    colcon-mixin

# Bootstrap rosdep
RUN rosdep init && rosdep update

# Setup colcon mixin and metadata
RUN colcon mixin add default \
      https://raw.githubusercontent.com/colcon/colcon-mixin-repository/master/index.yaml && \
    colcon mixin update && \
    colcon metadata add default \
      https://raw.githubusercontent.com/colcon/colcon-metadata-repository/master/index.yaml && \
    colcon metadata update

# Install ROS2 Jazzy
RUN apt-get update -y
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get install -y ros-jazzy-ros-base

# Install Radler dependencies
RUN apt-get update -y && apt-get install -y \
    cmake \
    python3-pip \
    python3-full
RUN pip3 install --break-system-packages tarjan pyyaml pydot parsimonious

# Install Radler
RUN cd /opt && git clone https://github.com/karthiknukala/radler.git && \
    cd radler && git checkout modernizing

# Environment setup
ENV ROS2_DISTRO=jazzy
ENV ROS2_PREFIX=/opt/ros
ENV RADLER_DIR=/opt/radler

# Copy build script
COPY radler-build.sh /usr/local/bin/radler-build
RUN chmod +x /usr/local/bin/radler-build

# Working directory for builds
WORKDIR /output

ENTRYPOINT ["/usr/local/bin/radler-build"]
CMD ["--help"]

