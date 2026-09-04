.PHONY: test install uninstall

test:
	bash -n msi-profile-control install-system.sh gaming-setup.sh uninstall.sh msi-game-run
	python3 -m py_compile msi-profile-hotkeyd msi-profile-osd msi-profile-doctor configure-steam-cs2.py
	python3 -m unittest discover -s tests -v
	bash tests/test_backend.sh

install:
	./install-system.sh

uninstall:
	./uninstall.sh
