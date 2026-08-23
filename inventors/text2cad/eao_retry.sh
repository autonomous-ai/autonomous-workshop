#!/bin/bash
cd /root/text2cad
rm -f eao_retry.log
for i in $(seq 1 36); do
  ./img2print.py eao-rifle-input.png --slug eao-scrap-rifle-pp --backend partpacker > img2print_eao.log 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then echo "DONE attempt=$i" >> eao_retry.log; exit 0; fi
  if grep -q "ZeroGPU quota" img2print_eao.log; then
    echo "attempt=$i quota-blocked $(date -u +%H:%M)" >> eao_retry.log; sleep 1200
  else
    echo "FAILED-nonquota attempt=$i" >> eao_retry.log; exit $rc
  fi
done
echo "GAVE-UP after 36 attempts" >> eao_retry.log; exit 9
