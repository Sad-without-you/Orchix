import subprocess
from apps.updater_base import BaseUpdater
from utils.docker_utils import safe_docker_run


class TemplateUpdater(BaseUpdater):
    """Generic updater for JSON-template-defined apps."""

    def __init__(self, manifest, template):
        super().__init__(manifest)
        self.template = template

    def get_available_actions(self):
        return ['version_update']

    def version_update(self):
        """Pull latest image and recreate container."""
        container_name = self.app_name
        image = self.template.get('image', '')

        if not image:
            return False

        # Pull latest image (silently, progress shown by caller)
        result = safe_docker_run(
            ['docker', 'pull', image],
            capture_output=True,
            text=True
        )

        if result is None or result.returncode != 0:
            return False

        # Find compose file and recreate (silently, progress shown by caller)
        compose_file = self._find_compose_file(container_name)
        if compose_file:
            safe_docker_run(
                ['docker', 'compose', '-f', compose_file, 'down'],
                capture_output=True,
                text=True
            )
            result = safe_docker_run(
                ['docker', 'compose', '-f', compose_file, 'up', '-d'],
                capture_output=True,
                text=True
            )
            if result and result.returncode == 0:
                return True

        return False
