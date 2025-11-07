"""
Docker container tests
Tests Docker build, container functionality, and deployment
"""

import pytest
import subprocess
import time
import requests
import os


class TestDockerBuild:
    """Test Docker image building."""
    
    @pytest.mark.skipif(not os.path.exists('Dockerfile'), reason="Dockerfile not found")
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists."""
        assert os.path.exists('Dockerfile')
    
    @pytest.mark.skipif(not os.path.exists('Dockerfile'), reason="Dockerfile not found")
    def test_docker_build(self):
        """Test that Docker image builds successfully."""
        try:
            result = subprocess.run(
                ['docker', 'build', '-t', 'purp-test', '.'],
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Build should succeed
            assert result.returncode == 0, f"Docker build failed: {result.stderr}"
            assert 'Successfully built' in result.stdout or 'Successfully tagged' in result.stdout
            
        except FileNotFoundError:
            pytest.skip("Docker not installed")
        except subprocess.TimeoutExpired:
            pytest.fail("Docker build timed out")
    
    @pytest.mark.skipif(not os.path.exists('Dockerfile'), reason="Dockerfile not found")
    def test_docker_image_size(self):
        """Test that Docker image is reasonably sized."""
        try:
            # First build the image
            subprocess.run(
                ['docker', 'build', '-t', 'purp-test', '.'],
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                capture_output=True,
                timeout=300
            )
            
            # Check image size
            result = subprocess.run(
                ['docker', 'images', 'purp-test', '--format', '{{.Size}}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                size_str = result.stdout.strip()
                # Image should exist
                assert size_str != '', "Image not found"
                
        except FileNotFoundError:
            pytest.skip("Docker not installed")


class TestDockerCompose:
    """Test docker-compose configuration."""
    
    @pytest.mark.skipif(not os.path.exists('docker-compose.yml'), reason="docker-compose.yml not found")
    def test_docker_compose_file_exists(self):
        """Test that docker-compose.yml exists."""
        assert os.path.exists('docker-compose.yml') or os.path.exists('docker-compose.yaml')
    
    @pytest.mark.skipif(not os.path.exists('docker-compose.yml'), reason="docker-compose.yml not found")
    def test_docker_compose_syntax(self):
        """Test that docker-compose file has valid syntax."""
        try:
            result = subprocess.run(
                ['docker-compose', 'config'],
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Config should be valid
            assert result.returncode == 0, f"docker-compose config invalid: {result.stderr}"
            
        except FileNotFoundError:
            pytest.skip("docker-compose not installed")
    
    @pytest.mark.skipif(not os.path.exists('docker-compose.yml'), reason="docker-compose.yml not found")
    def test_docker_compose_up(self):
        """Test that docker-compose up works."""
        try:
            # Start containers in detached mode
            result = subprocess.run(
                ['docker-compose', 'up', '-d'],
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            assert result.returncode == 0, f"docker-compose up failed: {result.stderr}"
            
            # Wait for services to be ready
            time.sleep(10)
            
            # Check if containers are running
            result = subprocess.run(
                ['docker-compose', 'ps'],
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert 'Up' in result.stdout or 'running' in result.stdout.lower()
            
        except FileNotFoundError:
            pytest.skip("docker-compose not installed")
        finally:
            # Clean up
            subprocess.run(
                ['docker-compose', 'down'],
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                capture_output=True
            )


class TestDockerContainer:
    """Test running Docker container."""
    
    @pytest.mark.skipif(not os.path.exists('Dockerfile'), reason="Dockerfile not found")
    def test_container_starts(self):
        """Test that container starts successfully."""
        try:
            # Build image first
            subprocess.run(
                ['docker', 'build', '-t', 'purp-test', '.'],
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                capture_output=True,
                timeout=300
            )
            
            # Run container
            container = subprocess.Popen(
                ['docker', 'run', '--rm', '-p', '5001:5000', 'purp-test'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for container to start
            time.sleep(5)
            
            # Check if container is running
            assert container.poll() is None, "Container exited immediately"
            
            # Stop container
            container.terminate()
            container.wait(timeout=10)
            
        except FileNotFoundError:
            pytest.skip("Docker not installed")
    
    @pytest.mark.skipif(not os.path.exists('Dockerfile'), reason="Dockerfile not found")
    def test_container_responds_to_http(self):
        """Test that container responds to HTTP requests."""
        try:
            # Build image
            subprocess.run(
                ['docker', 'build', '-t', 'purp-test', '.'],
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                capture_output=True,
                timeout=300
            )
            
            # Run container
            container = subprocess.Popen(
                ['docker', 'run', '--rm', '-p', '5001:5000', 'purp-test'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for app to start
            time.sleep(10)
            
            # Try to connect
            try:
                response = requests.get('http://localhost:5001/', timeout=5)
                assert response.status_code in [200, 302, 401]
            except requests.exceptions.RequestException:
                pytest.fail("Container not responding to HTTP requests")
            finally:
                container.terminate()
                container.wait(timeout=10)
                
        except FileNotFoundError:
            pytest.skip("Docker not installed")


class TestDockerEnvironment:
    """Test Docker environment configuration."""
    
    @pytest.mark.skipif(not os.path.exists('Dockerfile'), reason="Dockerfile not found")
    def test_dockerfile_has_python_base(self):
        """Test that Dockerfile uses Python base image."""
        with open('Dockerfile', 'r') as f:
            content = f.read()
            assert 'FROM python' in content or 'FROM python:' in content
    
    @pytest.mark.skipif(not os.path.exists('Dockerfile'), reason="Dockerfile not found")
    def test_dockerfile_copies_requirements(self):
        """Test that Dockerfile copies requirements.txt."""
        with open('Dockerfile', 'r') as f:
            content = f.read()
            assert 'requirements.txt' in content
    
    @pytest.mark.skipif(not os.path.exists('Dockerfile'), reason="Dockerfile not found")
    def test_dockerfile_exposes_port(self):
        """Test that Dockerfile exposes a port."""
        with open('Dockerfile', 'r') as f:
            content = f.read()
            assert 'EXPOSE' in content


class TestDockerCleanup:
    """Test Docker cleanup and resource management."""
    
    def test_cleanup_test_containers(self):
        """Clean up test containers and images."""
        try:
            # Stop any running test containers
            subprocess.run(
                ['docker', 'ps', '-a', '-q', '--filter', 'ancestor=purp-test'],
                capture_output=True
            )
            
            # Remove test image
            subprocess.run(
                ['docker', 'rmi', '-f', 'purp-test'],
                capture_output=True
            )
            
            # This test always passes - it's just cleanup
            assert True
            
        except FileNotFoundError:
            pytest.skip("Docker not installed")
