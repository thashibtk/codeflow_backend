import docker
import tempfile
import os
import time
import shutil
from pathlib import Path
from django.conf import settings

def execute_code(language, code, command=None):
    """
    Execute code in a sandbox using Docker.
    
    Args:
        language (str): Programming language to use
        code (str): The code to execute
        command (str): Optional command to run instead of the default
        
    Returns:
        tuple: (stdout, stderr, exit_code, execution_time)
    """
    # Get Docker image mapping from settings or use default
    DOCKER_IMAGE_MAPPING = getattr(settings, 'DOCKER_IMAGE_MAPPING', {
        'python': 'python:3.10-slim',
        'javascript': 'node:18-alpine',
        'typescript': 'node:18-alpine',
        'java': 'openjdk:17-slim',
        'cpp': 'gcc:11.2',
        'c': 'gcc:11.2',
        'ruby': 'ruby:3.1-slim',
        'go': 'golang:1.19-alpine',
        'rust': 'rust:1.65-slim',
        'php': 'php:8.1-cli',
    })
    
    # Get execution timeout from settings or use default (30 seconds)
    EXECUTION_TIMEOUT = getattr(settings, 'DOCKER_EXECUTION_TIMEOUT', 30)
    
    # Create a temporary directory for code files
    temp_dir = tempfile.mkdtemp(prefix=f"code_exec_{language}_")
    
    try:
        # Get Docker client
        client = docker.from_env()
        
        # Get the appropriate Docker image for the language
        image_name = DOCKER_IMAGE_MAPPING.get(language)
        if not image_name:
            return "", f"Unsupported language: {language}", 1, 0
        
        # Create the main code file based on language
        main_file = get_main_filename(language)
        main_path = os.path.join(temp_dir, main_file)
        
        with open(main_path, 'w') as f:
            f.write(code)
        
        # Prepare command to run
        if command and command.strip():
            cmd = command
        else:
            cmd = get_default_command(language, main_file)
        
        # Start execution timer
        start_time = time.time()
        
        # Run the code inside Docker container
        container = client.containers.run(
            image_name,
            cmd,
            volumes={temp_dir: {'bind': '/code', 'mode': 'rw'}},
            working_dir='/code',
            network_disabled=True,  # Disable network access for security
            mem_limit='256m',       # Limit memory to prevent DoS
            cpu_period=100000,      # Limit CPU usage
            cpu_quota=25000,        # 25% of CPU
            detach=True,
            remove=False
        )
        
        # Wait for container to finish with timeout
        try:
            container.wait(timeout=EXECUTION_TIMEOUT)
        except docker.errors.APIError:
            container.kill()
            return "", "Execution timed out", 124, EXECUTION_TIMEOUT
        
        # Get execution results
        stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
        stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')
        
        container_info = client.api.inspect_container(container.id)
        exit_code = container_info['State']['ExitCode']
        
        # Clean up the container
        container.remove()
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        return stdout, stderr, exit_code, execution_time
        
    except docker.errors.ImageNotFound:
        return "", f"Docker image for {language} not found", 1, 0
    except docker.errors.APIError as e:
        return "", f"Docker API error: {str(e)}", 1, 0
    except Exception as e:
        return "", f"Error executing code: {str(e)}", 1, 0
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

def get_main_filename(language):
    """Return the appropriate filename for the given language."""
    file_extensions = {
        'python': 'main.py',
        'javascript': 'main.js',
        'typescript': 'main.ts',
        'java': 'Main.java',
        'cpp': 'main.cpp',
        'c': 'main.c',
        'ruby': 'main.rb',
        'go': 'main.go',
        'rust': 'main.rs',
        'php': 'main.php',
    }
    return file_extensions.get(language, 'main.txt')

def get_default_command(language, main_file):
    """Return the default command to execute code in the given language."""
    commands = {
        'python': f'python {main_file}',
        'javascript': f'node {main_file}',
        'typescript': f'npx ts-node {main_file}',
        'java': 'javac Main.java && java Main',
        'cpp': f'g++ -std=c++17 {main_file} -o main && ./main',
        'c': f'gcc {main_file} -o main && ./main',
        'ruby': f'ruby {main_file}',
        'go': f'go run {main_file}',
        'rust': f'rustc {main_file} -o main && ./main',
        'php': f'php {main_file}',
    }
    return commands.get(language, f'cat {main_file}')
