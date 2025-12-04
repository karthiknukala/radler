# This file is part of Radler.
#
# Radler is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Radler is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Radler.  If not, see <http://www.gnu.org/licenses/>.

'''
@license: GPLv3

Created on May, 2014

@author: Léonard Gérard leonard.gerard@sri.com

@license: GPLv3

This file is part of Radler.

Radler is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Radler is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Radler.  If not, see <http://www.gnu.org/licenses/>.
'''

from pathlib import Path
from time import sleep
import sys

import argparse

from radler import exports
from radler.astutils.names import NonExistingIdent, ExistingIdent
from radler.astutils.tools import ensure_dir
from radler.instrumentation import analyzer
from radler.radlr import wd, errors, infos, alias, \
    language, objectfile, types, settings, structs, orderast, \
    workspace, gather
from radler.radlr.cgen import packagen
from radler.radlr.errors import log_err, internal_error, log1, error_noloc
from radler.radlr.parser import Semantics
from radler.radlr.plantgen import channels, plantcompute
from radler.radlr.plantgen.dump import dump_formatters, dump_filters
from radler.radlr.ros import rospackage, rosplant
from radler.radlr.dockergen import dockergen
from radler.radlr.workspace import ws_rospath


class Exit(Exception):
    def __init__(self, error_code, msg):
        self.error_code = error_code
        self.msg = msg

def internal_call(fun, *args, **dargs):
    try:
        v = fun(*args, **dargs)
        return Exit(v, "success")
    except Exit as e:
        return e

def resolve_node(node):
    try:
        if infos.ast:
            return infos.ast._namespace.resolve(node) #@UndefinedVariable
        else:
            return infos.root_namespace.resolve(node)
    except NonExistingIdent:
        raise Exit(-4, "Could not find the node " + node)

def resolve_plant(plant):
    plant = resolve_node(plant)
    if not plant._kind == 'plant':
        raise Exit(-5, 'Can\'t generate the plant, "{}" is not a plant'
                       ''.format(plant))
    return plant

def prepare_radl_source(filename):
    source = Path(filename)
    if not source.exists():
        raise Exit(-3, "The source file {} doesn't exist.".format(str(source)))
    if source.suffix != '.radl':
        raise Exit(-3, "The source file needs to have .radl suffix, {} given."
                "".format(str(source)))
    if not source.is_file():
        raise Exit(-3, str(source) + "isn't a valid file.")
    try: #We ensure the file is readable.
        source.open('r').close()
    except:
        raise Exit(-3, "The source file isn't readable.")
    infos.source_file = source

    infos.module_base_path = source.resolve().parent

def prepare_workspace(ws_dir):
    ws_dir = Path(ws_dir)
    if not ws_dir.is_dir():
        raise Exit(-2, "The workspace directory {} doesn't exist.\n"
                "You can change it using the --ws_dir option."
                "".format(ws_dir))
    infos.ws_dir = ws_dir

def load_object_files(obj_filenames):
    for of in obj_filenames:
        f = Path(of).resolve()
        if f.suffix != '.radlo':
            raise Exit(-1, "Object files need to have .radlo suffix, {} given."
                           "".format(str(f)))
        if not f.is_file():
            raise Exit(-1, str(f) + " isn't a valid file.")
        objectfile.load(f)


def obj_version(object_file=None, **_):
    try:
        o = objectfile.obj_open(Path(object_file))
    except:
        raise Exit(-1, 'Invalid object file.')
    raise Exit(0, 'Object version {} with language version {}.'
                  ''.format(o.obj_version, o.lang_version))


def obj_compatibility(object_file=None, **_):
    """
    Note that it returns 0 (False in Python but True in Bash) when the
    object (object_file) is compatible.
    """
    try:
        o = objectfile.obj_open(Path(object_file))
    except:
        raise Exit(-1, 'Invalid object file {}.'.format(object_file))
    if o.check_compat():
        raise Exit(0, "The object file {} is compatible.".format(object_file))
    else:
        raise Exit(-1, "The object file {} is incompatible.".format(object_file))

def load_pervasives(pervasives_dir=None, **_):
    if pervasives_dir is None:
        internal_error("can't call without pervasives_dir")
    pervasives_dir = Path(pervasives_dir)
    infos.pervasives_dir = pervasives_dir
    radl_file = pervasives_dir / 'radl.radl'
    radl_obj = pervasives_dir / 'radl.radlo'
    radl_mod = pervasives_dir / 'radlast_4_radl'
    if (radl_mod.is_dir()
        and radl_obj.is_file()
        and 0 == internal_call(obj_compatibility,
                               object_file=str(radl_obj), **dict(_)).error_code):
        # The radl_mod dir exists, the rald_obj too and the object is compatible
        objectfile.load(radl_obj)
    else: # Something isn't right let's compile pervasives
        log1("Compiling pervasives")
        args = dict(_) # Make a copy of the arguments as baseline
        args.update({  # Change arguments to compile pervasives
            'ws_dir'          : pervasives_dir,
            'no_pervasives'   : True,
            'pervasives_dir'  : str(pervasives_dir),
            'radl_file'       : str(radl_file),
            'object_files'    : None,
            'object_dest'     : str(radl_obj),
            'ROS'             : True,
            'relative_links'  : True
            })
        e = internal_call(compile_source, **args)
        if e.error_code != 0:
            raise e
    return 0

def compile_source(ws_dir=None, no_pervasives=None, pervasives_dir=None,
                   radl_file=None, object_files=None, object_dest=None,
                   plant=None, ROS=None, docker=None, ros_distro=None,
                   ros_domain_id=None, relative_links=None, **_):
    if not no_pervasives:
        #Ensure pervasives are correct
        #Beware that it calls compile_source and thus change modify infos,
        # -> It needs to be done before everything else.
        load_pervasives(pervasives_dir, **_)

    prepare_workspace(ws_dir)

    if not no_pervasives:
        workspace.ws_link_pervasives()
        if ROS:
            ensure_dir(ws_rospath(''))
            workspace.ws_link_rospervasives()

    prepare_radl_source(radl_file)

    if object_files:
        load_object_files(object_files)

    infos.relative_links = relative_links

    ########
    # Bootstrap the semantics from the language definition.
    ########

    infos.semantics = Semantics(language)

    # #saving the bootsrap is not possible since pickle doesn't pickle functions.
    # #so... tree_to_ast and ast_checker are not pickable.
    # #Maybe by mixing pickling and marshaling of __code__ of the functions
    # #is possible, but for now....
    # sem_file = infos.script_dir / 'semantics.pickle'
    # try:
    #     with sem_file.open('rb') as f:
    #         infos.semantics = pickle.load(f)
    # except Exception:
    #     args.force_bootstrap = True
    #
    # if args.force_bootstrap or infos.semantics.lang_version != language.version:
    #     infos.semantics = Semantics(language)
    #     log3('Bootstrapping')
    #     with sem_file.open('wb') as f:
    #         pickle.dump(infos.semantics, f)

    ########
    # Parse
    ########
    try:
        qname = infos.root_namespace.qualify(infos.source_file.stem)
    except ExistingIdent:
        error_noloc("Can't compile source file {},\n"
                    "a module with name {} is already loaded."
                    "".format(infos.source_file, infos.source_file.stem))
    with infos.source_file.open() as f:
        infos.ast = infos.semantics(f.read(), qname, infos.root_namespace)

    settings.do_pass(infos.ast)

    ######## Freeze #######
    # From here, the ast is "structurally frozen",
    # No new nodes/children are added and nodes keep their address.
    # This allow cross referencing, etc.
    ########

    #Transparent alias to forget about them.
    #Idents are replaced by aliases to ensure a local name to everything.
    alias.do_pass(infos.ast, infos.root_namespace)

    # Checks
    orderast.do_pass(infos.ast)
    structs.do_pass(infos.ast)
    types.typecheck(infos.ast)

    # Gather information
    gather.do_pass(infos.ast)
    wd.do_pass(infos.ast)

    # Generate the module package radlast (with the C ast and the rest)a
    packagen.do_pass(infos.ast)

    if plant:
        plant = resolve_plant(plant)
        plantinfo = plantcompute.do_pass(plant)
    else:
        plantinfo = None

    # ROS files generation
    if ROS:
        rospackage.do_pass(infos.ast, plantinfo)

    # Docker files generation
    if docker:
        if not plantinfo:
            raise Exit(-6, "Docker generation requires a plant. Use --plant to specify one.")
        package_name = infos.ast._name
        package_folder = ws_rospath(package_name)
        distro = ros_distro if ros_distro else 'jazzy'
        domain_id = ros_domain_id if ros_domain_id else 0
        dockergen.do_pass(plantinfo, package_name, package_folder, 
                         ros_distro=distro, ros_domain_id=domain_id)

    #Object file generation
    destobjf = None
    if object_dest: #Use user given path
        destobjf = infos.calling_dir / object_dest
    else: #Use default path
        destobjf = infos.ws_dir / (infos.source_file.stem + '.radlo')

    if destobjf: #Write the object file
        objectfile.save(infos.ast, destobjf)

    #indicate that the module is now loaded
    infos.loaded_modules.append(infos.ast._qname)  # @UndefinedVariable
    return 0


def analyze(log_file=None, instrument=None, nodes=None,
            follow=None, refresh_every=None, **_):
    a = analyzer(instrument, nodes)
    def report():
        print('--------------------------------------------------------------------------------')
        print(str(a))
    with (sys.stdin if log_file == '-' else open(log_file)) as file:
        line = file.readline()
        if follow:
            try:
                counter = 0
                while True:
                    a.parse(line)
                    counter += 1
                    if counter > refresh_every:
                        report()
                        counter = 0
                    line = file.readline()
                    while not line:
                        # We loop here since readline may return while the file
                        #   is still growing (non conforming pipes, etc).
                        report()
                        sleep(0.2)
                        line = file.readline()
            except KeyboardInterrupt:
                pass
        else:
            while line:
                a.parse(line)
                line = file.readline()
    report()
    return 0

def dump_node(node=None, formatter=None, filter_pred=None,
              object_files=None, pervasives_dir=None,
              no_pervasives=None, **_):
    if not no_pervasives:
        #Ensure pervasives are correct
        #Beware that it calls compile_source and thus change modify infos,
        # -> It needs to be done before everything else.
        load_pervasives(pervasives_dir, **_)
    if object_files:
        load_object_files(object_files)
    node = resolve_node(node)
    dump_formatters[formatter](node, dump_filters[filter_pred])
    return 0


def plantdot(dot_file=None, plant=None,
             object_files=None, pervasives_dir=None, no_pervasives=None, **_):
    if not no_pervasives:
        #Ensure pervasives are correct
        #Beware that it calls compile_source and thus change modify infos,
        # -> It needs to be done before everything else.
        load_pervasives(pervasives_dir, **_)
    if object_files:
        load_object_files(object_files)
    plant = resolve_plant(plant)
    plantinfo = plantcompute.do_pass(plant)
    dot = exports.plant2dot(plantinfo)
#    with (open(dot_file)) as file:
#        file.print(dot)


def init_project(name=None, path=None, lang=None, **_):
    """Initialize a new Radler project with a hello world template."""
    import os
    
    # Default to current directory if no path given
    if path is None:
        path = Path.cwd()
    else:
        path = Path(path)
    
    # Default name to directory name
    if name is None:
        name = path.name if path.name else "hello"
    
    # Sanitize name (no spaces, lowercase for consistency)
    name = name.replace(" ", "_").replace("-", "_").lower()
    
    # Default language to C++
    if lang is None:
        lang = 'cpp'
    
    # Create directory structure
    project_dir = path
    src_dir = project_dir / "src"
    
    if not project_dir.exists():
        project_dir.mkdir(parents=True)
    
    src_dir.mkdir(exist_ok=True)
    
    radl_file = project_dir / f"{name}.radl"
    
    # Check if files already exist
    if radl_file.exists():
        raise Exit(-1, f"Project already exists: {radl_file}")
    
    if lang == 'python':
        # Python templates
        radl_template = f'''# Radler project: {name}
# Generated by: radler init --lang python
#
# Build with:
#   ./radler.sh compile {name}.radl --plant plant --ROS
#
# Or with Docker:
#   docker run -v $(pwd):/project -v <radler_path>:/opt/radler -v /tmp/ros_ws:/output \\
#       radler/builder /project/{name}.radl --plant plant --docker

settings : module_settings {{
    MODULE_BASE_PATH "src"
}}

basic_rate : duration 1000msec

# Message topic definition
hello_msg : topic {{
    FIELDS
        count : int64 0
}}

# Publisher node - sends hello messages
talker : node {{
    PUBLISHES
        hello {{ TOPIC hello_msg }}
    PERIOD basic_rate
    PYTHON {{ FILENAME "talker.py" MODULE "talker" CLASS "Talker" }}
}}

# Subscriber node - receives hello messages  
listener : node {{
    SUBSCRIBES
        hello {{ TOPIC hello_msg MAXLATENCY 100msec }}
    PERIOD 100msec
    PYTHON {{ FILENAME "listener.py" MODULE "listener" CLASS "Listener" }}
}}

# System definition
sys1 : linux {{
    NODES_UID 1000
    IP 127.0.0.1
    NODES
        talker listener
}}

# Plant definition (deployment configuration)
plant : plant {{
    MACHINES
        local_machine {{
            OS sys1
        }}
}}
'''

        # Python talker template
        talker_py_template = '''#!/usr/bin/env python3
"""
Talker node - Python implementation
Publishes incrementing counter values
"""


class Talker:
    """Talker node that publishes incrementing counter values"""
    
    def __init__(self):
        """Initialize the talker with a counter"""
        self.counter = 0
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        """
        Step function called periodically by the ROS2 node
        
        Args:
            radl_in: Input structure with subscriptions (not used by talker)
            radl_in_flags: Input flags for subscriptions (not used by talker)
            radl_out: Output structure with publications
            radl_out_flags: Output flags for publications
        """
        # Set the output data
        radl_out.hello.count = self.counter
        self.counter += 1
        
        # Print for debugging (flush=True for Docker compatibility)
        print(f"Sent {radl_out.hello.count}", flush=True)
'''

        # Python listener template
        listener_py_template = '''#!/usr/bin/env python3
"""
Listener node - Python implementation
Receives and prints counter values
"""


class Listener:
    """Listener node that receives and prints counter values"""
    
    def __init__(self):
        """Initialize the listener"""
        pass
    
    def step(self, radl_in, radl_in_flags, radl_out, radl_out_flags):
        """
        Step function called periodically by the ROS2 node
        
        Args:
            radl_in: Input structure with subscriptions
            radl_in_flags: Input flags for subscriptions
            radl_out: Output structure with publications (not used by listener)
            radl_out_flags: Output flags for publications (not used by listener)
        """
        # Flag constants for checking message validity
        RADL_STALE = 3
        RADL_TIMEOUT = 48
        
        # Check if we have valid data (not stale or timed out)
        if not (radl_in_flags.hello & RADL_STALE) and not (radl_in_flags.hello & RADL_TIMEOUT):
            if radl_in.hello is not None:
                print(f"Received {radl_in.hello.count}", flush=True)
'''

        # Write Python files
        with open(radl_file, 'w') as f:
            f.write(radl_template)
        
        with open(src_dir / "talker.py", 'w') as f:
            f.write(talker_py_template)
        
        with open(src_dir / "listener.py", 'w') as f:
            f.write(listener_py_template)
        
        print(f"""
✓ Created Radler Python project: {name}

Files created:
  {radl_file}
  {src_dir}/talker.py
  {src_dir}/listener.py

Next steps:

  # Option 1: Build with Docker (no ROS installation needed)
  docker run -v $(pwd):/project \\
             -v <path-to-radler>:/opt/radler \\
             -v /tmp/ros_ws:/output \\
             radler/builder /project/{name}.radl --plant plant --docker
  
  cd /tmp/ros_ws/src/ros/{name}/docker
  docker-compose build
  docker-compose up

  # Option 2: Build natively (requires ROS2 + colcon)
  ./radler.sh compile {name}.radl --plant plant --ROS
  cd <workspace>/src/ros/{name}
  colcon build
  source install/setup.bash
  ros2 run {name} talker &
  ros2 run {name} listener
""")
    
    else:
        # C++ templates (default)
        radl_template = f'''# Radler project: {name}
# Generated by: radler init
#
# Build with:
#   ./radler.sh compile {name}.radl --plant plant --ROS
#
# Or with Docker:
#   docker run -v $(pwd):/project -v <radler_path>:/opt/radler -v /tmp/ros_ws:/output \\
#       radler/builder /project/{name}.radl --plant plant --docker

settings : module_settings {{
    MODULE_BASE_PATH "src"
}}

basic_rate : duration 1000msec

# Message topic definition
hello_msg : topic {{
    FIELDS
        count : int64 0
}}

# Publisher node - sends hello messages
talker : node {{
    PUBLISHES
        hello {{ TOPIC hello_msg }}
    PERIOD basic_rate
    CXX {{ HEADER "talker.h" FILENAME "talker.cpp" CLASS "Talker" }}
}}

# Subscriber node - receives hello messages  
listener : node {{
    SUBSCRIBES
        hello {{ TOPIC hello_msg MAXLATENCY 100msec }}
    PERIOD 100msec
    CXX {{ HEADER "listener.h" FILENAME "listener.cpp" CLASS "Listener" }}
}}

# System definition
sys1 : linux {{
    NODES_UID 1000
    IP 127.0.0.1
    NODES
        talker listener
}}

# Plant definition (deployment configuration)
plant : plant {{
    MACHINES
        local_machine {{
            OS sys1
        }}
}}
'''

        # Template for talker.h
        talker_h_template = '''#ifndef TALKER_H
#define TALKER_H

#include "radl__talker.h"

class Talker {
public:
    Talker();
    void step(const radl_in_t* in, const radl_in_flags_t* in_flags,
              radl_out_t* out, radl_out_flags_t* out_flags);

private:
    int counter_;
};

#endif // TALKER_H
'''

        # Template for talker.cpp
        talker_cpp_template = '''#include "talker.h"
#include <iostream>

Talker::Talker() : counter_(0) {
}

void Talker::step(const radl_in_t* in, const radl_in_flags_t* inflags,
                  radl_out_t* out, radl_out_flags_t* outflags) {
    // Increment and send counter
    out->hello->count = counter_++;
    
    std::cout << "Sent " << out->hello->count << std::endl;
}
'''

        # Template for listener.h
        listener_h_template = '''#ifndef LISTENER_H
#define LISTENER_H

#include "radl__listener.h"

class Listener {
public:
    Listener();
    void step(const radl_in_t* in, const radl_in_flags_t* in_flags,
              radl_out_t* out, radl_out_flags_t* out_flags);
};

#endif // LISTENER_H
'''

        # Template for listener.cpp
        listener_cpp_template = '''#include "listener.h"
#include <iostream>

Listener::Listener() {
}

void Listener::step(const radl_in_t* in, const radl_in_flags_t* inflags,
                    radl_out_t* out, radl_out_flags_t* outflags) {
    // Check if we received a valid message (not stale or timed out)
    if (!radl_is_stale(inflags->hello) && !radl_is_timeout(inflags->hello)) {
        std::cout << "Received " << in->hello->count << std::endl;
    }
}
'''

        # Write C++ files
        with open(radl_file, 'w') as f:
            f.write(radl_template)
        
        with open(src_dir / "talker.h", 'w') as f:
            f.write(talker_h_template)
        
        with open(src_dir / "talker.cpp", 'w') as f:
            f.write(talker_cpp_template)
        
        with open(src_dir / "listener.h", 'w') as f:
            f.write(listener_h_template)
        
        with open(src_dir / "listener.cpp", 'w') as f:
            f.write(listener_cpp_template)
        
        print(f"""
✓ Created Radler C++ project: {name}

Files created:
  {radl_file}
  {src_dir}/talker.h
  {src_dir}/talker.cpp
  {src_dir}/listener.h
  {src_dir}/listener.cpp

Next steps:

  # Option 1: Build with Docker (no ROS installation needed)
  docker run -v $(pwd):/project \\
             -v <path-to-radler>:/opt/radler \\
             -v /tmp/ros_ws:/output \\
             radler/builder /project/{name}.radl --plant plant --docker
  
  cd /tmp/ros_ws/src/ros/{name}/docker
  docker-compose build
  docker-compose up

  # Option 2: Build natively (requires ROS2 + colcon)
  ./radler.sh compile {name}.radl --plant plant --ROS
  cd <workspace>/src/ros/{name}
  colcon build
  source install/setup.bash
  ros2 run {name} talker &
  ros2 run {name} listener
""")
    
    return 0



if __name__ == "__main__":

    infos.calling_dir = Path.cwd()

    ########
    # Parse arguments
    ########
    p = argparse.ArgumentParser(prog='radler')
    p.add_argument('--version', action='version', version='%(prog)s ' + infos.radler_version)
    p.add_argument('--version_lang', action='version', version='RADL language ' + language.version)
    p.add_argument('--version_obj', action='version', version='Object language ' + objectfile.version)

    p.add_argument('--ws_dir', default='.', metavar='DIR', help='generate files in the DIR')

    p.add_argument('--warning_as_errors', action='store_true', help='warnings are treated as errors')
    vgrp = p.add_mutually_exclusive_group()
    vgrp.add_argument('--silent', dest='verb', action='store_const', const=-2, default=0, help='set verbosity to -2')
    vgrp.add_argument('--no_warn', dest='verb', action='store_const', const=-1, default=0, help='set verbosity to -1')
    vgrp.add_argument('-v', '--verbose', dest='verb', action='count', help='increase verbosity by 1')
    vgrp.add_argument('--verbosity', type=int, dest='verb', default=0, help='verbosity level, -1 errors, 0 warnings, + gives additional informations, level 2 and higher are mostly for debugging purposes.')
    p.add_argument('--continue_kamikaze', action='store_true', help='tries to recover from errors')
    #p.add_argument('--force_bootstrap', action='store_true', help='force regeneration of the p')

    subs_p = p.add_subparsers(dest='cmd', title='subcommands')

    objverp = subs_p.add_parser('obj_version', help='print the version of an object file')
    objverp.set_defaults(func=obj_version)
    objverp.add_argument('object_file', help='the object file to be analyzed')

    incomp = subs_p.add_parser('obj_compatible', help='return whether an object file is compatible')
    incomp.set_defaults(func=obj_compatibility)
    incomp.add_argument('object_file', help='the object file to be analyzed')

    compilep = subs_p.add_parser('compile', help='compile a radl file')
    compilep.set_defaults(func=compile_source)

    compilep.add_argument('--relative_links', action='store_true', help='when generating links, specify them relatively.')
    compilep.add_argument('--pervasives_dir', default=infos.pervasives_dir, help='specify the path of the pervasives module')
    compilep.add_argument('--no_pervasives', action='store_true', help='do not try to load the pervasives module (useful to compile the pervasives module).')
    compilep.add_argument('-o', '--object_dest', help='specify a path for the generated object file')
    compilep.add_argument('-O', '--object_files', action='append', help='compiled object files to load')
    compilep.add_argument('radl_file', metavar='modname.radl', help='the RADL source file defining a module named F')
    compilep.add_argument('--plant', help='specify the plant to be compiled.')
    compilep.add_argument('--ROS', action='store_true', help='Generate a ROS package for this module.')
    compilep.add_argument('--docker', action='store_true', help='Generate Dockerfiles and docker-compose.yml for container deployment. Requires --plant.')
    compilep.add_argument('--ros_distro', default='jazzy', help='ROS distribution for Docker containers (default: jazzy)')
    compilep.add_argument('--ros_domain_id', type=int, default=0, help='ROS domain ID for network isolation (default: 0)')
    compilep.add_argument('-i', '--instrument', default=[], nargs='*', choices=['step_timings', 'msg_timings'], help='Instrument the generated code to allow data to be collected at run time.\n    "step_timings" records the step function call timings.\n    "msg_timings" records the messages timings (this has quite a lot of impact since it increases the message sizes).')

    analyzep = subs_p.add_parser('analyze', help='compute statistics from the output of instrumented nodes.')
    analyzep.set_defaults(func=analyze)

    analyzep.add_argument('log_file', help='The log file to analyze, "-" to use stdin')
    analyzep.add_argument('-i', '--instrument', nargs='*', choices=['step_timings', 'msg_timings'], help='instruments to be considered during the analysis')
    analyzep.add_argument('--nodes', nargs='*', help='nodes to analyze, if none, any encountered node will be analyzed')
    analyzep.add_argument('-f', '--follow', action='store_true', help='nodes to analyze, if none, any encountered node will be analyzed')
    analyzep.add_argument('--refresh_every', type=int, default=1000, help='nodes to analyze, if none, any encountered node will be analyzed')

    dumpp = subs_p.add_parser('dump', help='dump a node.')
    dumpp.set_defaults(func=dump_node)

    dumpp.add_argument('node', help='name/qname of the node to dump.')
    dumpp.add_argument('--formatter', choices=dump_formatters.keys(), default='json', help='output formatting')
    dumpp.add_argument('-O', '--object_files', action='append', help='compiled object files to load')
    dumpp.add_argument('--pervasives_dir', default=infos.pervasives_dir, help='specify the path of the pervasives module')
    dumpp.add_argument('--no_pervasives', action='store_true', help='do not try to load the pervasives module (useful to compile the pervasives module).')
    dumpp.add_argument('--filter_pred', choices=dump_filters.keys(), default='none')


    plantdotp = subs_p.add_parser('plantdot', help='generate a dot file representing the plant.')
    plantdotp.set_defaults(func=plantdot)

    plantdotp.add_argument('-O', '--object_files', action='append', help='compiled object files to load')
    plantdotp.add_argument('--pervasives_dir', default=infos.pervasives_dir, help='specify the path of the pervasives module')
    plantdotp.add_argument('--no_pervasives', action='store_true', help='do not try to load the pervasives module (useful to compile the pervasives module).')
    plantdotp.add_argument('--plant', help='specify the plant to be compiled')
    #plantdotp.add_argument('-o', '--dot_file', help='specify a path for the generated dot file')

    initp = subs_p.add_parser('init', help='initialize a new Radler project with a hello world template')
    initp.set_defaults(func=init_project)
    initp.add_argument('name', nargs='?', help='project name (defaults to directory name)')
    initp.add_argument('--path', default='.', help='directory to create project in (default: current directory)')
    initp.add_argument('--lang', choices=['cpp', 'python'], default='cpp', help='programming language for node implementations (default: cpp)')

    args = p.parse_args()

    errors.continue_when_errors = args.continue_kamikaze
    errors.warning_as_errors = args.warning_as_errors
    errors.verbosity_level = args.verb

    if 'instrument' in args:
        infos.instrumentation = len(args.instrument) > 0
        infos.instrument_step_timings = 'step_timings' in args.instrument
        infos.instrument_msg_timings = 'msg_timings' in args.instrument

    try:
        cmd = args.func
    except AttributeError:
        print("You need to specify a subcommand.\n")
        p.print_help()
        exit(1)
    try:
        exit(cmd(**args.__dict__))
    except Exit as e:
        log_err(e.msg)
        exit(e.error_code)


