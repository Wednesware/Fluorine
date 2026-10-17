"""Build the archive layout expected by Nitrogen without generated files."""
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
package = 'fluorine'
version = (root / 'VERSION').read_text().strip()
output = root / 'dist' / f'{package}.zip'
output.parent.mkdir(exist_ok=True)
prefix = f'Fluorine-{version}'
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((root / package).rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            archive.write(path, f'{prefix}/{path.relative_to(root).as_posix()}')
    for name in ('README.md', 'LICENSE', 'CHANGELOG.md'):
        archive.write(root / name, f'{prefix}/{name}')
print(output)
