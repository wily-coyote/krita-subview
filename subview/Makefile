all: $(patsubst locale/%.po,locale/%/LC_MESSAGES/subview_docker.mo,$(wildcard locale/*.po))

locale/%/LC_MESSAGES/subview_docker.mo: locale/%.po
	mkdir -p $(dir $@)
	msgfmt -o $@ $<

messages.pot:
	xgettext --keyword=_ -o locale/messages.pot subview.py
