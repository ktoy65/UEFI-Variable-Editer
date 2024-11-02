bcfg boot rm 0

for %p in fs0 fs1 fs2 fs3 fs4 fs5 fs6 fs7 fs8 fs9
  if exist %p:\bootTools\setup_var.efi then
    echo find: %p
    %p:
    cd bootTools
    goto SETVAR
  endif
endfor

:SETVAR

setup_var.efi CpuSetup:0x334(1)=0x0
setup_var.efi CpuSetup:0x381(1)=0x0
setup_var.efi SaSetup:0x274(1)=0x1
setup_var.efi CpuSetup:0x2E3(1)=0x0
setup_var.efi CpuSetup:0x1D5(1)=0x0
setup_var.efi CpuSetup:0x132(2)=0x5a
setup_var.efi -r CpuSetup:0x7D(1)=0x0
