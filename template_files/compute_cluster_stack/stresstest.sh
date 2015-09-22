for i in `seq 1 2`; do
    echo "Stressing host $i"
    ssh -i compute_host_key.pem cirros@10.20.2.150 'dd if=/dev/zero of=/dev/null'
done
