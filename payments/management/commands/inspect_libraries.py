from django.core.management.base import BaseCommand
from pathlib import Path
import asyncio


class Command(BaseCommand):
    help = 'Inspect installed libraries for a project'
    
    def add_arguments(self, parser):
        parser.add_argument('project_id', type=str, help='Project UUID')
        parser.add_argument(
            '--export',
            action='store_true',
            help='Export formatted list'
        )
    
    def handle(self, *args, **options):
        project_id = options['project_id']
        export = options['export']
        
        try:
            project = Project.objects.get(id=project_id)
            
            # Get WebContainer info
            webcontainer = BrowserWebContainerManager()
            container_info = webcontainer.active_containers.get(project_id)
            
            if not container_info:
                self.stdout.write(
                    self.style.ERROR(f'WebContainer not running for project {project_id}')
                )
                return
            
            container_dir = Path(container_info['directory'])
            library_manager = LibraryManager(
                project_id,
                project.framework,
                container_dir
            )
            
            if export:
                # Export formatted list
                formatted = asyncio.run(library_manager.export_libraries_list())
                self.stdout.write(formatted)
            else:
                # Show JSON data
                libraries = asyncio.run(library_manager.get_installed_external_libraries())
                
                self.stdout.write(self.style.SUCCESS(f'\nProject: {project.title}'))
                self.stdout.write(f'Framework: {project.framework}')
                self.stdout.write(f'\nDependencies ({len(libraries["dependencies"])}):')
                for name, version in libraries['dependencies'].items():
                    self.stdout.write(f'  • {name}: {version}')
                
                self.stdout.write(f'\nDev Dependencies ({len(libraries["devDependencies"])}):')
                for name, version in libraries['devDependencies'].items():
                    self.stdout.write(f'  • {name}: {version}')
                
                self.stdout.write(self.style.SUCCESS('\n✅ Done'))
                
        except Project.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Project {project_id} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )