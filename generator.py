import os
from shutil import which
import subprocess
import yaml
import argparse
import shutil
import glob


class Repo:
    url: str
    name: str

    def __init__(self, url, name):
        self.url = url
        self.name = name
        pass


# directories of subprojects. subject to change
git_dronecan_dsdlc = Repo(
    "https://github.com/dronecan/dronecan_dsdlc.git", "dronecan_dsdlc")
git_dronecan_pydronecan = Repo(
    "https://github.com/dronecan/pydronecan.git", "pydronecan")
git_dronecan_dsdl = Repo("https://github.com/dronecan/DSDL.git", "DSDL")
git_dronecan_libcanard = Repo(
    "https://github.com/dronecan/libcanard.git", "libcanard")


clone_repositories = [git_dronecan_dsdlc, git_dronecan_pydronecan,
                      git_dronecan_dsdl, git_dronecan_libcanard]


def tool_exist(name):
    """Check whether `name` is on PATH and marked as executable."""
    return which(name) is not None


def git_clone_repo(repo: Repo):
    print(f"Attempting to clone repository: {repo.url}")

    output_dir = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), repo.name)

    if (os.path.exists(output_dir)):
        print(
            f"Repository {repo.name} is already cloned and is in folder {output_dir}")
    else:
        return_code = subprocess.call(
            ['git', 'clone', repo.url, output_dir], shell=True)
        if (return_code != 0):
            print(f"Failed to fetch {repo.url}. Tool is terminating.")
            exit(-1)
        else:
            print("Success!")


def clone_all(clone_repositories):

    if tool_exist("git"):
        git_version = subprocess.check_output(
            ['git', '--version']).decode("utf-8")
        print(f"Found {git_version}")

        for (index, repo) in enumerate(clone_repositories):
            print(
                f"\nRepository [{index+1}/{len(clone_repositories)}]: {repo.name}")
            git_clone_repo(repo)

    else:
        print("Git is not present in the system")
        exit(-1)


def generate_sources(export_dsdl, input_dir, output_dir):

    if (os.path.exists(input_dir)):

        immediate_subdirectories = os.scandir(input_dir)

        lib = ["DSDL/uavcan"]  # required basic libraries from DSDL

        for directory in immediate_subdirectories:
            lib.append(f"{input_dir}/{directory.name}")

        return_code = subprocess.call(
            ['python', 'dronecan_dsdlc/dronecan_dsdlc.py', "-O", f"{output_dir}", *lib], shell=True)

        if export_dsdl:

            if (os.path.exists("DSDL_out")):
                shutil.rmtree("DSDL_out")

            shutil.copytree('DSDL', 'DSDL_out', dirs_exist_ok=True)
            shutil.copytree(f'{input_dir}', 'DSDL_out', dirs_exist_ok=True)

    else:
        print(
            f"""Path "{input_dir}" do not exists. Create this directory first.""")
        exit(-1)


parser = argparse.ArgumentParser()
parser.add_argument('--input-dir', '-I', action='store', required=True)
parser.add_argument('--output-dir', '-O', action='store', required=True)
parser.add_argument('--export-dsdl', action='store_true')

args = parser.parse_args()


def create_makefile(input_dir, output_dir):
    if (os.path.exists(f"{output_dir}/include") and os.path.exists(f"{output_dir}/src")):
        sources_list = []
        # for (dir_path, dir_names, file_names) in os.walk(f"{output_dir}/src"):
        #     sources_list.extend(file_names)
        sources_list = [f"src/{f}" for f in os.listdir(f"{output_dir}/src")]

    sources_string = "\n".join(sources_list)

    makefile = f"""
    project(DSDL)

    add_library(${{PROJECT_NAME}}
    {sources_string}
    )

    target_link_libraries(${{PROJECT_NAME}} PUBLIC canard)
    target_include_directories(${{PROJECT_NAME}} PUBLIC ${{CMAKE_CURRENT_SOURCE_DIR}}/include)
    set(CMAKE_C_FLAGS "${{CMAKE_C_FLAGS}} -O0 -g -Wall -I. -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")

    """

    print(makefile)

    f = open(f"{output_dir}/CMakeLists.txt", "w")
    f.write(makefile)
    f.close()




clone_all(clone_repositories)

generate_sources(args.export_dsdl, args.input_dir, args.output_dir)

create_makefile(args.input_dir, args.output_dir)