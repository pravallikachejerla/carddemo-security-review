#!/bin/bash
# Check if tunnel is running on the system
if [ $(ps f | grep -c "2121:") == 1 ]
then 
  echo "FTP Tunnel to Ensono not running."
  exit 
fi

# Security Review R9 note:
# This script uses tnftp over the local tunnel entry point (localhost:2121),
# which means this client-to-local-port hop is plaintext FTP traffic.
# That plaintext exposure exists regardless of how the tunnel itself is
# configured. Before production use, confirm the tunnel terminates TLS/SSH
# properly end-to-end and evaluate whether the remote endpoint can be moved
# from plain FTP-in-tunnel to SFTP/FTPS.

file_name=$1
file_extension=$2

echo $file_name $file_extension

if [ $file_extension != ".jcl" ]
then
 echo "Only files with jcl extension can be submitted on mainframe"
 exit
fi

tnftp localhost 2121 <<EOF
pwd
quote site filetype=JES
put $file_name
bye
EOF