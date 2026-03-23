import paramiko, sys
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('45.84.138.48', username='root', key_filename='C:/Users/sulta/.ssh/id_ed25519', timeout=15)
script = """
mongosh -u admin -p 'AdminPass123!' --authenticationDatabase admin --eval '
    var cdb = db.getSiblingDB("admin");
    print("=== COMMENTS (last 3) ===");
    cdb.comments.find().sort({_id:-1}).limit(3).forEach(function(d) { printjson(d); });
    print("=== EVENTS (last 2) ===");
    cdb.events.find().sort({_id:-1}).limit(2).forEach(function(d) { printjson(d); });
' 2>/dev/null
"""
stdin, stdout, stderr = client.exec_command(script, timeout=30)
sys.stdout.buffer.write(stdout.read())
client.close()
