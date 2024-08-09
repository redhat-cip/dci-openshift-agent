NAME = dci-openshift-agent
BUILDROOT =
DATADIR = /usr/share
SYSCONFDIR = /etc
BINDIR = /usr/bin
SHAREDSTATEDIR = /var/lib
UNITDIR = /usr/lib/systemd/system

install:
	install -p -D -m 644 ansible.cfg $(BUILDROOT)$(DATADIR)/dci-openshift-agent/ansible.cfg
	install -p -D -m 644 dci-openshift-agent.yml  $(BUILDROOT)$(DATADIR)/dci-openshift-agent/dci-openshift-agent.yml
	install -p -D -m 644 dcirc.sh.dist $(BUILDROOT)$(SYSCONFDIR)/dci-openshift-agent/dcirc.sh.dist

	for hook in hooks/*.yml; do \
	  install -p -D -m 644 $$hook  $(BUILDROOT)$(SYSCONFDIR)/dci-openshift-agent/$$hook; \
	done

	install -p -D -m 644 settings.yml $(BUILDROOT)$(SYSCONFDIR)/dci-openshift-agent/settings.yml

	for play in plays/*.yml; \
	  do install -p -D -m 644 $$play $(BUILDROOT)$(DATADIR)/dci-openshift-agent/$$play; \
	done

	for script in plays/scripts/*; do \
	  install -p -D -m 755 $$script $(BUILDROOT)$(DATADIR)/dci-openshift-agent/$$script; \
	done

	for cru_play in plays/crucible/*.yml; do \
	  install -p -D -m 755 $$cru_play $(BUILDROOT)$(DATADIR)/dci-openshift-agent/$$cru_play; \
	done

	for template in plays/templates/*; do \
	  install -p -D -m 755 $$template $(BUILDROOT)$(DATADIR)/dci-openshift-agent/$$template; \
	done

	install -dm 755 "$(BUILDROOT)$(DATADIR)/dci-openshift-agent/utils/"
	install -Dm 755 utils/cleanup-scripts/*{.sh,.py} "$(BUILDROOT)$(DATADIR)/dci-openshift-agent/utils/"

	for plugin in action_plugins/*.py; \
	  do install -p -D -m 644 $$plugin $(BUILDROOT)$(DATADIR)/dci-openshift-agent/$$plugin; \
	done

	install -p -D -m 644 group_vars/all $(BUILDROOT)$(DATADIR)/dci-openshift-agent/group_vars/all

	install -p -D -m 644 systemd/$(NAME).service $(BUILDROOT)$(UNITDIR)/$(NAME).service
	install -p -D -m 644 systemd/$(NAME).timer $(BUILDROOT)$(UNITDIR)/$(NAME).timer

	install -p -D -m 440 dci-openshift-agent.sudo $(BUILDROOT)$(SYSCONFDIR)/sudoers.d/$(NAME)
	install -p -d -m 755 $(BUILDROOT)/$(SHAREDSTATEDIR)/$(NAME)
	find samples -type f -exec install -Dm 644 "{}" "$(BUILDROOT)$(SHAREDSTATEDIR)/dci-openshift-agent/{}" \;
	chmod 755 "$(BUILDROOT)$(SHAREDSTATEDIR)/dci-openshift-agent/samples/ocp_on_libvirt/ci.sh"
	install -p -D -m 755 dci-openshift-agent-ctl $(BUILDROOT)$(BINDIR)/dci-openshift-agent-ctl

	install -p -D -m 755 dci-check-change $(BUILDROOT)$(BINDIR)/dci-check-change

	for cmd in extract-dependencies send-feedback test-runner; do \
	  install -v -p -D -m 755 $$cmd $(BUILDROOT)$(DATADIR)/dci-openshift-agent/; \
	done
