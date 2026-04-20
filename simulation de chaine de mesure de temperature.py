#!/usr/bin/env python
# coding: utf-8

# In[3]:


#Simulateur de chaîne de mesure complète
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider, Button

# Les constattes
SENSIBILITE_TC  = 41.276e-6
TEMP_AMBIANTE   = 25.0
TEMP_VARIATION  = 5.0
BRUIT_THERMIQUE = 1e-6
ADC_VREF        = 2.5

# Paramètres de simulation
PARAMS = {
    "freq_variation": 0.5,
    "bruit_pct": 5.0,
    "gain": 100.0,
    "fc": 10.0,
    "bits": 12
}

# Les paramètres de temps
DUREE = 10
FS = 500
DT = 1/FS
t = np.arange(0, DUREE, DT)

# Les fonctions
def simuler_temperature(t, freq, bruit_pct):
    signal = TEMP_AMBIANTE + TEMP_VARIATION*np.sin(2*np.pi*freq*t)
    bruit = TEMP_VARIATION*(bruit_pct/100)*np.random.randn(len(t))
    return signal + bruit


def thermocouple(T):
    return SENSIBILITE_TC*T + BRUIT_THERMIQUE*np.random.randn(len(T))


def ampli(v,gain):
    return np.clip(v*gain,-5,5)


def filtre(signal,fc):
    rc = 1/(2*np.pi*fc)
    alpha = DT/(rc+DT)
    y = np.zeros(len(signal))
    y[0]=signal[0]
    for i in range(1,len(signal)):
        y[i]=y[i-1]+alpha*(signal[i]-y[i-1])
    return y


def adc(v,bits):
    lsb=(2*ADC_VREF)/(2**bits)
    v=np.clip(v,-ADC_VREF,ADC_VREF)
    return np.round(v/lsb)*lsb


def to_temp(v,gain):
    return v/(gain*SENSIBILITE_TC)

# La partie calcul

def calcul(p):
    T = simuler_temperature(t,p["freq_variation"],p["bruit_pct"])
    v = thermocouple(T)
    v_amp = ampli(v,p["gain"])
    v_filt = filtre(v_amp,p["fc"])
    v_adc = adc(v_filt,p["bits"])
    T_adc = to_temp(v_adc,p["gain"])
    return T, v*1e6, v_amp*1e3, T_adc

# Les figures
fig = plt.figure(figsize=(14,9))
gs = gridspec.GridSpec(5,2)

ax1=fig.add_subplot(gs[0,0])
ax2=fig.add_subplot(gs[1,0])
ax3=fig.add_subplot(gs[2,0])
ax4=fig.add_subplot(gs[3,0])
axM=fig.add_subplot(gs[:,1])
axM.axis('off')

# >>> Ajout d'espace entre les graphes
plt.subplots_adjust(hspace=0.9)

# Initial
T, V, A, Tadc = calcul(PARAMS)

l1,=ax1.plot(t,T)
l2,=ax2.plot(t,V)
l3,=ax3.plot(t,A)
l4,=ax4.plot(t,Tadc)

# >>> Les titres de graphes et les axes de temps
ax1.set_title("Température réelle (°C)")
ax2.set_title("Tension thermocouple (µV)")
ax3.set_title("Signal amplifié (mV)")
ax4.set_title("Température reconstruite (°C)")

ax1.set_xlabel("Temps (s)")
ax2.set_xlabel("Temps (s)")
ax3.set_xlabel("Temps (s)")
ax4.set_xlabel("Temps (s)")

# >>> Amélioration visuelle
for ax in [ax1, ax2, ax3, ax4]:
    ax.grid(True)
    ax.set_xlim(0, DUREE)

# Les metriques
txt=axM.text(0.1,0.9,"")

def update_metrics(p,Tadc):
    snr = 20*np.log10(100/max(p['bruit_pct'],1e-6))
    res = ((2*ADC_VREF)/(2**p['bits']))/(p['gain']*SENSIBILITE_TC)*1000
    txt.set_text(
        f"Moyenne: {np.mean(Tadc):.2f} °C\n"
        f"SNR: {snr:.1f} dB\n"
        f"Résolution: {res:.2f} m°C\n"
        f"Niveaux ADC: {2**p['bits']}"
    )

update_metrics(PARAMS,Tadc)

# Les sliders
sliders={}
params_list=[("freq_variation",0.1,5),("bruit_pct",0,30),("gain",10,500),("fc",1,50),("bits",8,16)]

for i,(k,a,b) in enumerate(params_list):
    ax_s=plt.axes([0.1,0.02+i*0.04,0.3,0.02])
    sliders[k]=Slider(ax_s,k,a,b,valinit=PARAMS[k])

# Uptade
def update(val):
    for k in sliders:
        PARAMS[k]=sliders[k].val
    T,V,A,Tadc = calcul(PARAMS)
    l1.set_ydata(T)
    l2.set_ydata(V)
    l3.set_ydata(A)
    l4.set_ydata(Tadc)
    update_metrics(PARAMS,Tadc)
    fig.canvas.draw_idle()

for s in sliders.values():
    s.on_changed(update)

# Export CSV
def export(event):
    data=np.column_stack((t,l4.get_ydata()))
    np.savetxt("resultats.csv",data,delimiter=",",header="t,Temp",comments="")

btn_ax=plt.axes([0.8,0.02,0.1,0.03])
btn=Button(btn_ax,"Export CSV")
btn.on_clicked(export)

plt.show()


# In[ ]:




