.PHONY: setup test build package doctor clean

setup:
	./install.command

test:
	.venv/bin/python -m compileall -q main.py doctor.py src tests
	.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
	.venv/bin/python main.py --version | grep -Eq '^DualCPY macOS [0-9]+\.[0-9]+\.[0-9]+$$'
	zsh -n install.command run.command scripts/*.sh

build: test
	.venv/bin/python build.py
	codesign --verify --deep --strict "dist/DualCPY macOS.app"

package: build
	./scripts/package_release.sh unsigned

doctor:
	.venv/bin/python doctor.py

clean:
	rm -rf "build" "dist" "release"
