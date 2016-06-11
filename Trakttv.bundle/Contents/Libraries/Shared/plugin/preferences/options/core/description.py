class Description(object):
    def __init__(self, description, options):
        self.description = description
        self.options = options

    def build(self):
        sections = []

        if self.description:
            sections.append(self.description)

        if self.options:
            sections.append("\n".join([
                "| | |",
                "|-|-|",
                "\n".join([
                    "| **%s** | %s |" % option
                    for option in self.options
                ])
            ]))

        return "\n\n".join(sections)
