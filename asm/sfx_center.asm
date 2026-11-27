; Mars Matrix Overpowered: sound effects play centered.
;
; The Z80 sound driver (mmx.01) sets a voice's QSound pan from its pan value
; (ix+$47), 0..$20 -> QSound pan register $80+voice = $0110 + value
; ($110 = hard left, $120 = center, $130 = hard right). Sound effects carry 0
; (hard left); with QSound's 3D processing off (Build 7) they came out of the
; left speaker only. Music keeps its own panning.
;
; Both pan sites (key-on at $0466 and $0871) originally do:
;     ld e,(ix+47h) / ld a,(0F008h) / or a / jr nz,+2 / ld e,10h   (11 bytes)
; i.e. use the voice's pan unless the game's MONO setting ($F008 = 0) is on.
; They now call sfx_pan instead. A voice is a sound effect when (ix+1) != 0
; (the same test trap15's volume patch uses at $1FEC).
;
; Assembled by overpowered.py with trap15's bundled AS; the Z80 is not encrypted.

	CPU	Z80

SFX_CENTER	:= 10h		; pan value for sound effects (10h = center)
FREE_BASE	:= 7100h	; free (zero) Z80 ROM after trap15's code at 7000h

	ORG	0466h
sc_hook1:
	call	sfx_pan
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
sc_hook1_end:

	ORG	0871h
sc_hook2:
	call	sfx_pan
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
sc_hook2_end:

	ORG	FREE_BASE
sfx_pan:
	ld	e,(ix+47h)	; voice pan (music)
	ld	a,(0F008h)	; 0 = MONO setting: always center
	or	a
	jr	z,.center
	ld	a,(ix+1)	; non-zero = sound effect
	or	a
	ret	z
.center:
	ld	e,SFX_CENTER
	ret
sc_end:
