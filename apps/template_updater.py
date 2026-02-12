import subprocess
from apps.updater_base import BaseUpdater
from utils.docker_progress import run_docker_with_progress


class TemplateUpdater(BaseUpdater):
    """Generic updater for JSON-template-defined apps."""

    def __init__(self, manifest, template):
        super().__init__(manifest)
        self.template = template

    def get_available_actions(self):
        return ['version_update']

    def version_update(self):
        """Pull latest image and recreate container."""
        try:
            from cli.ui import show_step_detail
        except ImportError:
            show_step_detail = print

        container_name = self.app_name
        image = self.template.get('image', '')

        if not image:
            show_step_detail("No image defined in template")
            return False

        # Pull latest image
        result = run_docker_with_progress(
            ['docker', 'pull', image],
            f"Pulling {image}",
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode != 0:
            show_step_detail(f"Pull failed: {result.stderr}")
            return False

        # Find compose file and recreate
        compose_file = self._find_compose_file(container_name)
        if compose_file:
            subprocess.run(
                ['docker', 'compose', '-f', compose_file, 'down'],
                capture_output=True, text=True
            )
            result = run_docker_with_progress(
                ['docker', 'compose', '-f', compose_file, 'up', '-d'],
                "Restarting container with new image",
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                show_step_detail(f"{container_name} updated successfully!")
                return True

        return False
