# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 20:59:20 2023

@author: Junghyun
"""

import numpy as np

# 모든 함수는 e (dielectric function) 를 기준으로 계산한다.
def lorentzian(w, w0, wp, g) :
    if w0 == 0 : w0 = 0.0000001 # devide by 0 방지
    e = (wp*wp)/( (w0*w0)-(w*w)-(1j*g*w) )
    return e

def drude(w, wp, g) : # 맞는지 확인 필요
    if g == 0 : g = 0.0000001
    return (wp*wp)/((-1j*g-w)*w)

def local_drude(w, C, wp, g) :
    return drude(w, wp, g) * (1 + C*(1-(w*w/(g*g)))/(1+(w*w/(g*g))) )

def to_sigma(w, e) :
    return (w*e/(4*np.pi*1j))*(np.pi/15)

def to_refraction_index(w, e) : # 함수의 통일성을 위해 그냥 w는 받기로...
    return np.sqrt(e)

# Tauc-Lorentz Oscillator 계산에 필요한 함수들들
# 주어진 수식에 필요한 함수들 정의
def a_ln(E, E0, Eg, C):
    return (Eg**2 - E0**2) * E**2 + Eg**2 * C**2 - E0**2 * (E0**2 + 3 * Eg**2)

def a_atan(E, E0, Eg, C):
    return (E**2 - E0**2) * (E0**2 + Eg**2) + Eg**2 * C**2

def alpha(E0, C):
    return np.sqrt(4 * E0**2 - C**2)

def gamma(E0, C):
    return np.sqrt(E0**2 - C**2 / 2)

def zeta4(E, E0, C):
    gamma_val = gamma(E0, C)
    alpha_val = alpha(E0, C)
    return (E**2 - gamma_val**2)**2 + (alpha_val**2 * C**2) / 4

# Real part 계산
def real_part_Tauc_Lorentz(E, E0, Eg, A, C):
    a_ln_val = a_ln(E, E0, Eg, C)
    a_atan_val = a_atan(E, E0, Eg, C)
    alpha_val = alpha(E0, C)
    gamma_val = gamma(E0, C)
    zeta4_val = zeta4(E, E0, C)

    term1 = (A * C / (np.pi * zeta4_val)) * (a_ln_val / (2 * alpha_val * E0)) * np.log((E0**2 + Eg**2 + alpha_val * Eg) / (E0**2 + Eg**2 - alpha_val * Eg))
    term2 = -(A / (np.pi * zeta4_val)) * (a_atan_val / E0) * (np.pi-np.arctan((alpha_val + 2 * Eg) / C) + np.arctan((alpha_val - 2 * Eg) / C))
    term3 = (4 * A * E0 / (np.pi * zeta4_val * alpha_val)) * Eg * (E**2 - gamma_val**2) * (np.arctan((alpha_val + 2 * Eg) / C) + np.arctan((alpha_val - 2 * Eg) / C))
    term4 = -(A * E0 * C / (np.pi * zeta4_val)) * (E**2 + Eg**2) / E * np.log(np.abs((E - Eg) / (E + Eg)))
    term5 = (2 * A * E0 * C / (np.pi * zeta4_val)) * Eg * np.log(np.abs((E - Eg)) * (E + Eg) / np.sqrt((E0**2 - Eg**2)**2 + Eg**2 * C**2))

    return term1 + term2 + term3 + term4 + term5

def imaginary_part_Tauc_Lorentz(E, E0, Eg, A, C):
    # 허수부 계산
    epsilon_2 = np.zeros_like(E)
    for i in range(len(E)) :
        if E[i] > Eg:
            epsilon_2[i] = A * E0 * C * (E[i] - Eg)**2 / (E[i] * ((E[i]**2 - E0**2)**2 + C**2 * E[i]**2))
        else:
            epsilon_2[i] = 0
    return epsilon_2

def Tauc_Lorentz(w, w0, wg, A, C) : 
    # w0, wg, A, C는 모두 wavenumber 단위.
    # Energy단위로 바꾸어서 계산한다.
    E = w/8065.5
    E0 = w0/8065.5
    Eg = wg/8065.5
    A = A/8065.5
    C = C/8065.5

    e1 = real_part_Tauc_Lorentz(E, E0, Eg, A, C)
    e2 = imaginary_part_Tauc_Lorentz(E, E0, Eg, A, C)
    e = e1 + 1j*e2 # Dielectric func
    return e