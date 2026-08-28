# G4MEOVER ONE-X — DSI-Panel-Overlay bauen
#
# Das Overlay nutzt CPP-Includes (dt-bindings). Es wird daher erst mit dem
# C-Preprocessor aufgeloest und dann mit dtc zum .dtbo kompiliert.
#
#   make            -> rk3576-one-x-panel5.dtbo
#   make clean
#
# KDIR muss auf einen RK3576-Kernelbaum zeigen (fuer die dt-bindings-Header).
# Anpassen an die eigene Umgebung:
KDIR ?= /lib/modules/$(shell uname -r)/build

DTC      ?= dtc
CPP      ?= cpp
INCLUDES  = -I$(KDIR)/include -I$(KDIR)/scripts/dtc/include-prefixes

OVERLAY   = rk3576-one-x-panel5
SRC       = $(OVERLAY).dtso
PRE       = $(OVERLAY).pre.dts
OUT       = $(OVERLAY).dtbo

all: $(OUT)

$(PRE): $(SRC)
	$(CPP) -nostdinc $(INCLUDES) -undef -x assembler-with-cpp $< -o $@

$(OUT): $(PRE)
	$(DTC) -@ -I dts -O dtb -o $@ $<
	@echo "OK: $(OUT) gebaut. HINWEIS: VERIFY/HOLD-Stellen im Overlay muessen vor dem Flashen gesetzt sein."

clean:
	rm -f $(PRE) $(OUT)

.PHONY: all clean
