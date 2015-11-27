import click

@click.command()
@click.option('--hostname', prompt='Enter remote host name', default='localhost ', help='Remote host name')
def init_session(hostname):
    click.echo('You are now connected to %s' % hostname)
    
@click.command()
@click.option('--Document_UID', prompt='Enter the name of the docuent you wish to check out', default='filename')
def check_out(Document_UID):
    click.echo('You have checked out document %s' % Document_UID)
    
@click.command()
@click.option('--Document_UID', prompt='Enter the name of the document you wish to check in')
@click.option('--Security_Flag', prompt='Would you like to enable document (C)onfidentiality or (I)ntegrity', default='None')
def check_in(Document_UID, Security_Flag):
    click.echo('You have check in document %s' % Document_UID)
    click.echo('Document checked in with %s flag set' % Security_Flag)
    
@click.command()
@click.option('--Document_UID', prompt='Enter the name of the document you wish to delgate access to')
@click.option('--client', prompt='Which user would you like to share this document with')
@click.option('--time', prompt='When would you like this delegation to expire(in number of days)', default='Never')
@click.option('--permission', prompt='Would you like this user to be able to (R)ead this document or (W)rite and read', default='R')
@click.option('--PropogationFlag', prompt='Would you like this user to be able to allow others to access this document', default='No')
def delegate(Document_UID, client, time, permission, PropogationFlag):
    click.echo('You have succesfully granted %s the ability to %s to %s for %s days' % client, permission, Document_UID, time)
    
@click.command()
@click.option('--Document_UID', prompt='Enter the name of the document you wish to securely delete')
def safe_delete(Document_UID):
    click.echo('You have safely deleted %s' % Document_UID)
    
@click.command()
def terminate_session():
    click.echo('You have disconnected from the host')
    
if __name__ == '__main__':
    #check_out()
    #check_in()
    #init_session()
    terminate_session()
    
