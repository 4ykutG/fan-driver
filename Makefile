.PHONY: test install uninstall

test:
	bash -n msi-profile-control install-system.sh uninstall.sh
	python3 -m py_compile msi-profile-hotkeyd msi-profile-osd msi-profile-doctor msi-profile-monitor
	python3 -m unittest discover -s tests -v
	bash tests/test_backend.sh

install:
	./install-system.sh

uninstall:
	./uninstall.sh
