#!/bin/bash
# Radler Build Script
# Compiles a .radl file into ROS2 packages and optionally generates Docker artifacts.
#
# Usage:
#   radler-build <radl_file> [--plant <plant_name>] [--docker] [--build] [--sros2]
#
# Arguments:
#   radl_file           Path to the .radl source file
#   --plant NAME        Name of the plant to compile (default: plant)
#   --docker            Generate Dockerfiles and docker-compose.yml for each node
#   --build             Also run colcon build after generating ROS packages
#   --sros2             Setup SROS2 security keys
#   --help              Show this help message

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
PLANT_NAME="plant"
GENERATE_DOCKER=false
RUN_BUILD=false
SETUP_SROS2=false
RADL_FILE=""
OUTPUT_DIR="/output"

print_help() {
    echo "Radler Build Script"
    echo ""
    echo "Usage: radler-build <radl_file> [options]"
    echo ""
    echo "Arguments:"
    echo "  radl_file              Path to the .radl source file"
    echo ""
    echo "Options:"
    echo "  --plant NAME           Name of the plant to compile (default: plant)"
    echo "  --docker               Generate Dockerfiles and docker-compose.yml for each node"
    echo "  --build                Also run colcon build after generating ROS packages"
    echo "  --sros2                Setup SROS2 security keys"
    echo "  --output DIR           Output directory (default: /output)"
    echo "  --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Generate ROS packages only"
    echo "  radler-build /project/my_system.radl --plant plant"
    echo ""
    echo "  # Generate ROS packages and build them"
    echo "  radler-build /project/my_system.radl --plant plant --build"
    echo ""
    echo "  # Generate ROS packages + Docker artifacts"
    echo "  radler-build /project/my_system.radl --plant plant --docker"
    echo ""
    echo "  # Full build with Docker and SROS2"
    echo "  radler-build /project/my_system.radl --plant plant --docker --build --sros2"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --plant)
            PLANT_NAME="$2"
            shift 2
            ;;
        --docker)
            GENERATE_DOCKER=true
            shift
            ;;
        --build)
            RUN_BUILD=true
            shift
            ;;
        --sros2)
            SETUP_SROS2=true
            shift
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help|-h)
            print_help
            exit 0
            ;;
        -*)
            echo -e "${RED}Error: Unknown option $1${NC}"
            print_help
            exit 1
            ;;
        *)
            if [[ -z "$RADL_FILE" ]]; then
                RADL_FILE="$1"
            else
                echo -e "${RED}Error: Multiple .radl files specified${NC}"
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate inputs
if [[ -z "$RADL_FILE" ]]; then
    echo -e "${RED}Error: No .radl file specified${NC}"
    print_help
    exit 1
fi

if [[ ! -f "$RADL_FILE" ]]; then
    echo -e "${RED}Error: File not found: $RADL_FILE${NC}"
    exit 1
fi

# Setup ROS2 environment
echo -e "${GREEN}Setting up ROS2 environment...${NC}"
source "$ROS2_PREFIX/$ROS2_DISTRO/setup.bash"

# Create output directory structure
mkdir -p "$OUTPUT_DIR/src"

# Get the module name from the .radl filename
MODULE_NAME=$(basename "$RADL_FILE" .radl)

echo -e "${GREEN}Compiling $RADL_FILE...${NC}"
echo -e "  Plant: $PLANT_NAME"
echo -e "  Output: $OUTPUT_DIR"

# Build the radler command
RADLER_CMD="./radler.sh --ws_dir $OUTPUT_DIR/src compile $RADL_FILE --plant $PLANT_NAME --ROS"

# Add docker flag if requested
if [[ "$GENERATE_DOCKER" == true ]]; then
    RADLER_CMD="$RADLER_CMD --docker"
fi

# Run Radler to generate ROS packages (and optionally Docker artifacts)
cd "$RADLER_DIR"
echo -e "${GREEN}Running: $RADLER_CMD${NC}"
eval $RADLER_CMD

# If generating Docker, copy all dependencies into output
# (Docker build context can't follow symlinks outside the context)
if [[ "$GENERATE_DOCKER" == true ]]; then
    echo -e "${GREEN}Copying dependencies for Docker build...${NC}"
    cd "$OUTPUT_DIR/src"
    
    # Copy radler pervasives (radl_lib, radlast_4_radl, ros/radl)
    rm -f radl_lib 2>/dev/null  # Remove symlink if exists
    cp -r "$RADLER_DIR/../radl_lib" .
    
    rm -f radlast_4_radl 2>/dev/null
    cp -r "$RADLER_DIR/../pervasives/radlast_4_radl" .
    
    mkdir -p ros
    rm -f ros/radl 2>/dev/null
    cp -r "$RADLER_DIR/../pervasives/ros/radl" ros/
    
    # Replace any remaining symlinks with their targets
    find . -type l | while read link; do
        target=$(readlink -f "$link")
        if [[ -e "$target" ]]; then
            rm "$link"
            if [[ -d "$target" ]]; then
                cp -r "$target" "$link"
            else
                cp "$target" "$link"
            fi
        fi
    done
    
    echo -e "${GREEN}All files copied - ready for Docker build${NC}"
fi

# Build with colcon if requested
if [[ "$RUN_BUILD" == true ]]; then
    echo -e "${GREEN}Building with colcon...${NC}"
    cd "$OUTPUT_DIR"
    # Note: Don't use --symlink-install as it creates broken symlinks when
    # the build output is used outside this container
    colcon build
    
    echo -e "${GREEN}Build complete!${NC}"
    echo -e "To use the built packages, source the setup file:"
    echo -e "  source $OUTPUT_DIR/install/local_setup.bash"
fi

# Setup SROS2 if requested
if [[ "$SETUP_SROS2" == true ]]; then
    echo -e "${GREEN}Setting up SROS2 keys...${NC}"
    cd "$OUTPUT_DIR"
    ros2 security create_keystore sros2_keys
    
    # TODO: Create enclaves for each node based on plant definition
    echo -e "${YELLOW}Note: You may need to create additional enclaves for your nodes${NC}"
fi

# Find the ROS package directory (it's under ros/<module_name>)
ROS_PKG_DIR="$OUTPUT_DIR/src/ros/$MODULE_NAME"

# Print generated run instructions if docker mode was used
if [[ "$GENERATE_DOCKER" == true ]]; then
    INSTRUCTIONS_FILE="$ROS_PKG_DIR/docker/RUN_INSTRUCTIONS.txt"
    if [[ -f "$INSTRUCTIONS_FILE" ]]; then
        echo -e "${GREEN}"
        cat "$INSTRUCTIONS_FILE"
        echo -e "${NC}"
        echo -e "${YELLOW}Note: Replace <HOST_PATH> with your actual mount path (e.g., /tmp/ros_ws)${NC}"
        echo ""
        echo -e "${GREEN}The Docker containers will build ROS packages internally - no local ROS needed!${NC}"
    fi
elif [[ "$RUN_BUILD" == true ]]; then
    echo -e "${GREEN}Done!${NC}"
    echo ""
    echo "Generated and built files are in: $OUTPUT_DIR"
    echo ""
    echo "To run, start a container and use ros2 run:"
    echo "  docker run -it --rm -v <HOST_PATH>:/ros_ws ros:jazzy-ros-core bash"
    echo "  source /opt/ros/jazzy/setup.bash && source /ros_ws/install/local_setup.bash"
    echo "  ros2 run $MODULE_NAME <node_name>"
else
    echo -e "${GREEN}Done!${NC}"
    echo ""
    echo "Generated source files are in: $OUTPUT_DIR/src"
    echo ""
    echo "To build, use --build flag or run colcon build manually."
fi

