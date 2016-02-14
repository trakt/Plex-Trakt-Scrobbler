""" CLI integration. """

import click

VERBOSE = ['WARNING', 'INFO', 'DEBUG']


@click.group()
def cli():
    pass


@cli.command()
@click.option('--name', default=None, help="Select migration")
@click.option('--database', default=None, help="Database connection")
@click.option('--directory', default='migrations', help="Directory where migrations are stored")
@click.option('-v', '--verbose', count=True)
def migrate(name=None, database=None, directory=None, verbose=None):
    """ Run migrations. """
    from .core import Router

    router = Router(directory, DATABASE=database, LOGGING=VERBOSE[verbose])
    router.run(name)


@cli.command()
@click.argument('name')
@click.option('--database', default=None, help="Database connection")
@click.option('--directory', default='migrations', help="Directory where migrations are stored")
@click.option('-v', '--verbose', count=True)
def create(name, database=None, directory=None, verbose=None):
    """ Create migration. """
    from .core import Router

    router = Router(directory, DATABASE=database, LOGGING=VERBOSE[verbose])
    router.create(name)

if __name__ == '__main__':
    cli()
