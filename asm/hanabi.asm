; Mars Matrix Overpowered: the Dreamcast-only Arrange enemies Hanabi, Chubi, Shobi and TELPO.
;
; The Dreamcast Arrange layouts use class $74 "Hanabi" (firework), which has no
; arcade descriptor. Its code exists only in the Dreamcast program (SH-4, a
; mechanical translation of 68000 code), so it is translated back here:
;   Hanabi  (DC descriptor $8C1EE044): rises on its spawn script, bursts after
;           11 frames on screen (or when shot) into a bullet and 4 Chubi.
;   Chubi   ($8C1EE084): flies out, slows to a stop, turns to face the player
;           for 64 frames, then speeds off. Shot: bullet + 8 Shobi.
;   Shobi   ($8C1EE0C4): spirals out (angle +3/frame, speeding up). Shot: it
;           flashes for 8 frames, then pops into a bullet.
;
; Dreamcast -> arcade mapping used:
;   DC object word $1C/$1E   -> arcade $1A (speed) / $1C (angle)
;   DC $3C (hp) / $4C (score)-> arcade $52 / $60 (from descriptor +$28 / +$36)
;   DC private $54+n         -> arcade $68+n
;   DC byte n                -> arcade byte n^1 (the DC stores words little-endian)
;   DC calls: $8C03493C script step = $40B48, $8C034890 velocity = $D5786,
;   $8C0345CE hitbox = $119898, $8C0358A4 sprite (list 5) = $145A44 with $FF0B72,
;   $8C010262 bullet = $32276, $8C0344C6 sound = $151E5E, $8C035370 random = $1197F6,
;   $8C0136B8 spawn = $36456, $8C011208 explosion = $3930E,
;   $8C031E5C+$8C031FBE score = $3222A, $8C03312E player = $321E2,
;   $8C0367D2 angle to = $C4F56, $8C0348B2 turn toward = $11981E.
;   TELPO   ($8C1F0B90, class $75): warps in, flies on its script firing
;           5-bullet bursts from an attack slot, warps out.
; Chubi's DC glow effect is not ported, nor TELPO's marker sprite (drawn on
; list 4 every other frame when a player-struct flag is set).
;
; Code is encrypted by overpowered.py. The descriptors (hb_descs) are data.
; The sprite frames (SPR_TABLE, 3 x 32 frames x 16 bytes) are copied from the
; user's Dreamcast disc ($8C1ED9EC) by the Arrange import, never stored here.

	CPU		68000
	PADDING	OFF
	SUPMODE	ON

SCRIPT_STEP	:= $040B48
VELOCITY	:= $0D5786
HITBOX		:= $119898
SPR_ADD		:= $145A44
SPR_LIST	:= $FF0B72
BULLET		:= $032276
SOUND		:= $151E5E
RANDOM		:= $1197F6
SPAWN		:= $036456
SPREAD		:= $039328	; gold cube with a random spread (d0=x, d1=y, d4=size)
EXPLODE		:= $03930E	; gold cube drop: d0 x, d1 y, d4 size
SCORE		:= $03222A
PLAYER		:= $0321E2
ATAN		:= $0C4F56
TURN		:= $11981E
SPR_TABLE	:= $17F000	; Hanabi frames +$000, Chubi +$200, Shobi +$400
TP_TABLE	:= $17F600	; TELPO: 16 warp frames, body (+$100), marker (+$110)
SPR_ADD_NF	:= $145A22	; sprite add without the hit flash ($8C035408)
EFF_ALLOC	:= $03159E	; attack slots: d0 = count -> a0 ($8C1106D8 + $8C036274)
EFF_SET		:= $0315EE	; a0 = slots, d0 = slot offset, a1 = data ($8C036296)
EFF_TICK	:= $031648	; a0 = slots, a6 = owner ($8C036352)
EFF_FREE	:= $0315E0	; a0 = slots ($8C110796)
SHOT		:= $032CB8	; on-screen bullet: d0..d4 ($8C012648)
SHOT_FLASH	:= $031832	; bullet + muzzle flash ($8C013C00 / $8C013C68)
DEBRIS		:= $032362	; ($8C114350)
ZN_TABLE	:= $17F720	; Zan/Zc/Zz: 12 frames (spin)
SPR_LIST4	:= $FF0B6E	; sprite list 4
Z_EFF	:= $68		; Zan/Zc: DC $54, attack slots
Z_ANIM	:= $70		; Zan/Zc: DC $5C, spin counter
Z_KILLER := $72		; Zan/Zc: player that shot it (for the score)
ZZ_MASK	:= $6C		; Zz: DC $58, blink mask
ZZ_ADD	:= $6E		; Zz: DC $5A, speed step
T_EFF	:= $68		; TELPO: DC $54, attack slots
T_WARP	:= $70		; TELPO: DC $5C
T_STATE	:= $72		; TELPO: DC $5E

X	:= $12
Y	:= $16
SPEED	:= $1A
ANGLE	:= $1C
HP	:= $52
H_ANIM	:= $6C		; Hanabi: DC $58
H_TIME	:= $6E		; Hanabi: DC $5A
C_FACE	:= $70		; Chubi: DC $5C
C_STATE	:= $72		; Chubi: DC $5E
C_TIME	:= $74		; Chubi: DC $60
S_ANIM	:= $6C		; Shobi: DC $58

	ORG	$17D000

; ---------------------------------------------------------------- shared
hb_nop:
	rts

; draw the frame at a0 at the object's position (sprite list $FF0B72)
draw_one:
	move.w	X(a6),d0
	move.w	Y(a6),d1
	movem.l	d0-d1/a0-a1,-(a7)
	movea.l	(SPR_LIST).l,a1
	jsr	(SPR_ADD).l
	move.l	a1,(SPR_LIST).l
	movem.l	(a7)+,d0-d1/a0-a1
	rts

play22:
	clr.l	-(a7)
	clr.l	-(a7)
	move.w	#$16,-(a7)
	clr.w	-(a7)
	jsr	(SOUND).l
	lea	$C(a7),a7
	rts

; hitbox at (x - d2/2, y - d3/2), size d2 x d3
hitbox:
	move.w	X(a6),d0
	move.w	Y(a6),d1
	move.w	d2,d4
	lsr.w	#1,d4
	sub.w	d4,d0
	move.w	d3,d4
	lsr.w	#1,d4
	sub.w	d4,d1
	lea	(a6),a1
	jmp	(HITBOX).l

; d4 = explosion size
explode:
	movem.l	d0-d1/d4,-(a7)
	move.w	X(a6),d0
	move.w	Y(a6),d1
	jsr	(EXPLODE).l
	movem.l	(a7)+,d0-d1/d4
	rts

; move by angle/speed
move:
	move.w	ANGLE(a6),d0
	move.w	SPEED(a6),d1
	jsr	(VELOCITY).l
	add.l	d0,X(a6)
	add.l	d1,Y(a6)
	rts

; d0 = angle from the object to the player
aim:
	jsr	(PLAYER).l
	move.w	X(a0),d0
	move.w	Y(a0),d1
	sub.w	X(a6),d0
	sub.w	Y(a6),d1
	jmp	(ATAN).l

delete:
	ori.w	#$9000,$8(a6)
	rts

; ---------------------------------------------------------------- Hanabi
hb_init:
	move.w	#$6000,$8(a6)
	clr.w	H_ANIM(a6)
	move.w	#$18,SPEED(a6)
	move.w	#10,H_TIME(a6)
	rts

hb_update:
	jsr	(SCRIPT_STEP).l
	btst	#4,$9(a6)
	beq.s	.notyet
	cmpi.w	#248,Y(a6)
	bgt.s	delete
	cmpi.w	#-24,Y(a6)
	blt.s	delete
	cmpi.w	#416,X(a6)
	bgt.s	delete
	cmpi.w	#-32,X(a6)
	blt.s	delete
	bra.s	.on
.notyet:
	cmpi.w	#384,X(a6)
	bcc.s	.on
	cmpi.w	#224,Y(a6)
	bcc.s	.on
	bset	#4,$9(a6)
.on:
	moveq	#64,d2
	moveq	#48,d3
	bsr.w	hitbox
	addq.w	#8,H_ANIM(a6)
	bset	#4,$9(a6)
	beq.s	.end
	subq.w	#1,H_TIME(a6)
	bmi.s	.fire
	btst	#0,$F(a6)
	beq.s	.end
	ori.w	#4,$8(a6)
.end:
	rts
.fire:
	bsr.s	hb_burst
	bra.w	delete

; bullet, sound 22, 4 Chubi at 90-degree steps from a random angle
hb_burst:
	move.w	X(a6),d0
	move.w	Y(a6),d1
	moveq	#0,d2
	moveq	#0,d3
	move.l	#$4008,d4
	jsr	(BULLET).l
	bsr.w	play22
	jsr	(RANDOM).l
	moveq	#0,d2
	move.b	d0,d2
	move.w	X(a6),d0
	move.w	Y(a6),d1
	moveq	#48,d3
	moveq	#3,d5
.next:
	lea	(cb_desc).l,a0
	jsr	(SPAWN).l
	addi.w	#64,d2
	dbra	d5,.next
	rts

hb_draw:
	move.w	H_ANIM(a6),d2
	andi.w	#$1F0,d2
	lea	(SPR_TABLE).l,a0
	adda.w	d2,a0
	bra.w	draw_one

hb_hit:
	tst.w	HP(a6)
	bmi.s	.x
	sub.w	d0,HP(a6)
	bpl.s	.x
	jsr	(SCORE).l
	movem.l	d0-d7/a0-a1,-(a7)
	moveq	#3,d4
	bsr.w	explode
	bsr.s	hb_burst
	movem.l	(a7)+,d0-d7/a0-a1
	ori.w	#$9000,$8(a6)
.x:
	rts

; ---------------------------------------------------------------- Chubi
cb_init:
	move.w	#$6000,$8(a6)
	bset	#4,$9(a6)
	move.w	#$80,C_FACE(a6)
	clr.w	C_STATE(a6)
	clr.w	C_TIME(a6)
	rts

cb_update:
	bsr.w	move
	btst	#4,$9(a6)
	beq.s	.notyet
	cmpi.w	#240,Y(a6)
	bgt.w	delete
	cmpi.w	#-16,Y(a6)
	blt.w	delete
	cmpi.w	#400,X(a6)
	bgt.w	delete
	cmpi.w	#-16,X(a6)
	blt.w	delete
	bra.s	.on
.notyet:
	cmpi.w	#384,X(a6)
	bcc.s	.on
	cmpi.w	#224,Y(a6)
	bcc.s	.on
	bset	#4,$9(a6)
.on:
	moveq	#32,d2
	moveq	#32,d3
	bsr.w	hitbox
	move.w	C_STATE(a6),d0
	beq.s	.slow
	subq.w	#2,d0
	beq.s	.turn
	; state 4: keep facing the player, speed up
	bsr.w	aim
	move.w	C_FACE(a6),d1
	moveq	#1,d2
	jsr	(TURN).l
	move.w	d1,C_FACE(a6)
	addq.w	#1,SPEED(a6)
	rts
.slow:						; state 0: slow down to a stop
	subq.w	#2,SPEED(a6)
	bne.s	.x
	addq.w	#2,C_STATE(a6)
	move.w	#64,C_TIME(a6)
.x:
	rts
.turn:						; state 2: turn to face the player for 64 frames
	bsr.w	aim
	move.w	C_FACE(a6),d1
	moveq	#2,d2
	jsr	(TURN).l
	move.w	d1,C_FACE(a6)
	subq.w	#1,C_TIME(a6)
	bne.s	.x
	addq.w	#2,C_STATE(a6)
	rts

cb_draw:
	move.w	C_FACE(a6),d2
	addq.w	#4,d2
	add.w	d2,d2
	andi.w	#$1F0,d2
	lea	(SPR_TABLE+$200).l,a0
	adda.w	d2,a0
	bra.w	draw_one

cb_hit:
	tst.w	HP(a6)
	bmi.s	.x
	sub.w	d0,HP(a6)
	bpl.s	.x
	jsr	(SCORE).l
	movem.l	d0-d7/a0-a1,-(a7)
	move.w	X(a6),d0
	move.w	Y(a6),d1
	moveq	#0,d2
	moveq	#0,d3
	move.l	#$8003,d4
	btst	#0,$F(a6)
	beq.s	.b
	subi.l	#$4000,d4
.b:
	jsr	(BULLET).l
	bsr.w	play22
	moveq	#1,d4
	bsr.w	explode
	ori.w	#$9000,$8(a6)
	jsr	(RANDOM).l
	moveq	#0,d2
	move.b	d0,d2
	move.w	X(a6),d0
	move.w	Y(a6),d1
	moveq	#0,d3
	moveq	#7,d5
.next:
	lea	(sb_desc).l,a0
	jsr	(SPAWN).l
	addi.w	#32,d2
	dbra	d5,.next
	movem.l	(a7)+,d0-d7/a0-a1
.x:
	rts

; ---------------------------------------------------------------- Shobi
sb_init:
	move.w	#$6000,$8(a6)
	bset	#4,$9(a6)
	clr.w	S_ANIM(a6)
	jsr	(RANDOM).l
	andi.w	#15,d0
	add.w	d0,SPEED(a6)
	rts

sb_update:
	tst.w	HP(a6)
	bpl.s	.alive
	ori.w	#4,$8(a6)			; shot: flash, then pop
	addq.w	#1,HP(a6)
	bne.s	.alive
	move.w	X(a6),d0
	move.w	Y(a6),d1
	moveq	#0,d2
	moveq	#0,d3
	move.l	#$4001,d4
	btst	#0,$F(a6)
	beq.s	.b
	addi.l	#$4000,d4
.b:
	jsr	(BULLET).l
	bsr.w	play22
	moveq	#0,d4
	bsr.w	explode
	bra.w	delete
.alive:
	bsr.w	move
	btst	#4,$9(a6)
	beq.s	.notyet
	cmpi.w	#232,Y(a6)
	bgt.w	delete
	cmpi.w	#-8,Y(a6)
	blt.w	delete
	cmpi.w	#392,X(a6)
	bgt.w	delete
	cmpi.w	#-8,X(a6)
	blt.w	delete
	bra.s	.on
.notyet:
	cmpi.w	#384,X(a6)
	bcc.s	.on
	cmpi.w	#224,Y(a6)
	bcc.s	.on
	bset	#4,$9(a6)
.on:
	moveq	#16,d2
	moveq	#16,d3
	bsr.w	hitbox
	addq.w	#4,S_ANIM(a6)
	addq.w	#3,ANGLE(a6)
	btst	#0,$F(a6)
	beq.s	.x
	addq.w	#1,SPEED(a6)
.x:
	rts

sb_draw:
	move.w	S_ANIM(a6),d2
	andi.w	#$1F0,d2
	lea	(SPR_TABLE+$400).l,a0
	adda.w	d2,a0
	bra.w	draw_one

sb_hit:
	tst.w	HP(a6)
	bmi.s	.x
	sub.w	d0,HP(a6)
	bpl.s	.x
	jsr	(SCORE).l
	move.w	#-8,HP(a6)
	bclr	#6,$8(a6)
.x:
	rts

; ---------------------------------------------------------------- TELPO (class $75)
; Warps in (T_WARP 0 -> 16), flies on its spawn script with its attack slot
; running, warps out (16 -> 0) once the script sets bit 0 of $B, then deletes.
; Object bytes (DC byte n = arcade n^1): $A bit 0 = warp frames shown,
; $A bit 1 = stopped (set when shot), $B bit 7 = attack slot running,
; $B bit 0 = leave (set by the script).
tp_init:
	move.w	#$6000,$8(a6)
	moveq	#1,d0
	jsr	(EFF_ALLOC).l		; one attack slot
	move.l	a0,T_EFF(a6)
	moveq	#0,d0
	lea	(tp_eff).l,a1
	jsr	(EFF_SET).l
	clr.l	T_WARP(a6)		; T_WARP and T_STATE
	rts

tp_kill:
	movea.l	T_EFF(a6),a0
	jmp	(EFF_FREE).l

tp_update:
	tst.w	HP(a6)
	bpl.s	.alive
	ori.w	#4,$8(a6)		; shot: flash, then pop
	addq.w	#1,HP(a6)
	bne.s	.box
	move.w	X(a6),d0
	move.w	Y(a6),d1
	moveq	#0,d2
	moveq	#0,d3
	moveq	#8,d4
	jsr	(DEBRIS).l
	bsr.w	play22
	moveq	#2,d4
	bsr.w	explode
	bra.w	delete
.alive:
	btst	#7,$B(a6)
	beq.s	.box
	movea.l	T_EFF(a6),a0
	jsr	(EFF_TICK).l
.box:
	moveq	#64,d2
	moveq	#32,d3
	bsr.w	hitbox
	btst	#1,$A(a6)
	bne.s	.x
	move.w	T_STATE(a6),d0
	beq.s	.warpin
	subq.w	#2,d0
	beq.s	.fly
	bclr	#0,$A(a6)		; state 4: warp out
	subq.w	#1,T_WARP(a6)
	beq.w	delete
.x:
	rts
.warpin:				; state 0
	addq.w	#1,T_WARP(a6)
	cmpi.w	#16,T_WARP(a6)
	bne.s	.x
	bset	#0,$A(a6)
	bset	#7,$B(a6)
	addq.w	#2,T_STATE(a6)
	rts
.fly:					; state 2
	jsr	(SCRIPT_STEP).l
	btst	#4,$9(a6)
	beq.s	.notyet
	cmpi.w	#240,Y(a6)
	bgt.w	delete
	cmpi.w	#-16,Y(a6)
	blt.w	delete
	cmpi.w	#416,X(a6)
	bgt.w	delete
	cmpi.w	#-32,X(a6)
	blt.w	delete
	bra.s	.on
.notyet:
	cmpi.w	#384,X(a6)
	bcc.s	.on
	cmpi.w	#224,Y(a6)
	bcc.s	.on
	bset	#4,$9(a6)
.on:
	btst	#0,$B(a6)
	beq.s	.x
	addq.w	#2,T_STATE(a6)
	bclr	#7,$B(a6)
	rts

; attack: called by the slot engine ($31648) with d0/d1 = position, d2 = angle,
; d3 = speed, d4 = bullet type (DC $8C0F8DEC)
tp_fire:
	jsr	(SHOT).l
	subq.w	#1,d3
	move.w	#$2C0,d4
	jsr	(SHOT).l
	subq.w	#1,d3
	jsr	(SHOT).l
	subq.w	#1,d3
	jsr	(SHOT).l
	subq.w	#1,d3
	move.w	#$340,d4
	jmp	(SHOT_FLASH).l

tp_draw:
	cmpi.w	#7,T_WARP(a6)
	bcs.s	.nobody
	lea	(TP_TABLE+$100).l,a0	; body
	bsr.w	draw_one
.nobody:
	btst	#0,$A(a6)
	beq.s	.x
	move.w	T_WARP(a6),d2		; warp frame
	lsl.w	#4,d2
	lea	(TP_TABLE).l,a0
	adda.w	d2,a0
	move.w	X(a6),d0
	move.w	Y(a6),d1
	movem.l	d0-d1/a0-a1,-(a7)
	movea.l	(SPR_LIST).l,a1
	jsr	(SPR_ADD_NF).l
	move.l	a1,(SPR_LIST).l
	movem.l	(a7)+,d0-d1/a0-a1
.x:
	rts

tp_hit:
	tst.w	HP(a6)
	bmi.s	.x
	sub.w	d0,HP(a6)
	bpl.s	.x
	jsr	(SCORE).l
	move.w	#-8,HP(a6)
	bclr	#6,$8(a6)
	bset	#1,$A(a6)
	move.w	#$80,ANGLE(a6)
	move.w	#8,SPEED(a6)
.x:
	rts

; ---------------------------------------------------------------- Zan (class $76), Zz, Zc
; Zan flies its script firing 4-shot bursts and, every 16 frames while moving,
; leaves a Zz: a blinking after-image (Zan frame by speed) that spins up for
; 128 frames, then turns into a Zc, which flies off along the heading Zz took
; toward the player, speeding up and firing. Zan and Zc share draw/hit/kill.
; Shot: hp counts -8 -> 0, then the spin counter winds up to $C0 and it explodes.
zn_init:
	move.w	#$6000,$8(a6)
	lea	(zn_eff).l,a1
	bsr.s	z_slot
	clr.w	Z_ANIM(a6)
	move.w	#32,SPEED(a6)
	jsr	(RANDOM).l
	andi.w	#15,d0
	add.w	d0,SPEED(a6)
	rts

; one attack slot with the data at a1
z_slot:
	moveq	#1,d0
	jsr	(EFF_ALLOC).l
	move.l	a0,Z_EFF(a6)
	moveq	#0,d0
	jmp	(EFF_SET).l

zn_kill:
	movea.l	Z_EFF(a6),a0
	jmp	(EFF_FREE).l

; final explosion once the spin counter reaches $C0
z_blowup:
	move.w	Z_KILLER(a6),d1
	jsr	(SCORE).l
	bsr.w	play22
	moveq	#1,d4
	bsr.w	explode
	bra.w	delete

; bounds check for Zan/Zc (delete outside -16..400 / -16..240), on-screen flag
z_bounds:
	btst	#4,$9(a6)
	beq.s	.notyet
	cmpi.w	#240,Y(a6)
	bgt.s	.del
	cmpi.w	#-16,Y(a6)
	blt.s	.del
	cmpi.w	#400,X(a6)
	bgt.s	.del
	cmpi.w	#-16,X(a6)
	blt.s	.del
	moveq	#0,d0
	rts
.notyet:
	cmpi.w	#384,X(a6)
	bcc.s	.ok
	cmpi.w	#224,Y(a6)
	bcc.s	.ok
	bset	#4,$9(a6)
.ok:
	moveq	#0,d0
	rts
.del:
	ori.w	#$9000,$8(a6)
	moveq	#-1,d0
	rts

zn_update:
	btst	#0,$A(a6)
	beq.s	.alive
	addq.w	#1,HP(a6)			; shot
	bmi.s	.move
	addq.w	#4,Z_ANIM(a6)
	cmpi.w	#$C0,Z_ANIM(a6)
	bcc.w	z_blowup
	rts
.alive:
	movea.l	Z_EFF(a6),a0
	jsr	(EFF_TICK).l
.move:
	jsr	(SCRIPT_STEP).l
	bsr.s	z_bounds
	bmi.s	.x
	moveq	#32,d2
	moveq	#32,d3
	bsr.w	hitbox
	addq.w	#4,Z_ANIM(a6)
	andi.w	#$7F,Z_ANIM(a6)
	btst	#0,$A(a6)
	bne.s	.x
	tst.w	SPEED(a6)
	beq.s	.x
	moveq	#15,d0
	and.w	$E(a6),d0
	bne.s	.x
	move.w	X(a6),d0			; leave a Zz
	move.w	Y(a6),d1
	move.w	ANGLE(a6),d2
	moveq	#$70,d3
	and.w	Z_ANIM(a6),d3
	lea	(zz_desc).l,a0
	jsr	(SPAWN).l
.x:
	rts

; attack: 3 shots at speed d3, d3+1, d3+2, then one with a flash at d3+3 (DC $8C0FCED8)
zn_fire:
	jsr	(SHOT).l
	addq.w	#1,d3
	jsr	(SHOT).l
	addq.w	#1,d3
	jsr	(SHOT).l
	addq.w	#1,d3
	jmp	(SHOT_FLASH).l

zn_draw:
	move.w	Z_ANIM(a6),d2
	andi.w	#$F0,d2
	lea	(ZN_TABLE).l,a0
	adda.w	d2,a0
	bra.w	draw_one

zn_hit:
	tst.w	HP(a6)
	bmi.s	.x
	sub.w	d0,HP(a6)
	bpl.s	.x
	move.w	#-8,HP(a6)
	bset	#0,$A(a6)
	move.w	d1,Z_KILLER(a6)			; player, for the score at the end
.x:
	rts

zz_init:
	move.w	#$1800,$8(a6)
	bsr.w	aim
	move.w	d0,ANGLE(a6)
	move.w	#1,ZZ_MASK(a6)
	clr.w	ZZ_ADD(a6)
	rts

zz_update:
	move.w	ZZ_ADD(a6),d0
	add.w	d0,SPEED(a6)
	cmpi.w	#32,$E(a6)
	bne.s	.a
	move.w	#3,ZZ_MASK(a6)
	move.w	#4,ZZ_ADD(a6)
.a:
	cmpi.w	#64,$E(a6)
	bne.s	.b
	move.w	#7,ZZ_MASK(a6)
	move.w	#8,ZZ_ADD(a6)
.b:
	cmpi.w	#128,$E(a6)
	bne.s	.x
	move.w	X(a6),d0			; become a Zc
	move.w	Y(a6),d1
	move.w	ANGLE(a6),d2
	moveq	#0,d3
	lea	(zc_desc).l,a0
	jsr	(SPAWN).l
	bra.w	delete
.x:
	rts

zz_draw:
	move.w	$E(a6),d0
	and.w	ZZ_MASK(a6),d0
	bne.s	.x
	move.w	SPEED(a6),d2
	andi.w	#$70,d2
	lea	(ZN_TABLE).l,a0
	adda.w	d2,a0
	move.w	X(a6),d0
	move.w	Y(a6),d1
	movem.l	d0-d1/a0-a1,-(a7)
	movea.l	(SPR_LIST4).l,a1
	jsr	(SPR_ADD_NF).l
	move.l	a1,(SPR_LIST4).l
	movem.l	(a7)+,d0-d1/a0-a1
.x:
	rts

zc_init:
	move.w	#$6000,$8(a6)
	lea	(zc_eff).l,a1
	bsr.w	z_slot
	bset	#4,$9(a6)
	clr.w	Z_ANIM(a6)
	rts

zc_update:
	btst	#0,$A(a6)
	beq.s	.alive
	addq.w	#1,HP(a6)			; shot
	bmi.s	.move
	bset	#5,$B(a6)
	addq.w	#4,Z_ANIM(a6)
	cmpi.w	#$C0,Z_ANIM(a6)
	bcc.w	z_blowup
	bra.s	.bounds
.alive:
	movea.l	Z_EFF(a6),a0
	jsr	(EFF_TICK).l
	addi.w	#16,Z_ANIM(a6)
	andi.w	#$7F,Z_ANIM(a6)
.move:
	bsr.w	move
.bounds:
	bsr.w	z_bounds
	bmi.s	.x
	btst	#5,$B(a6)
	bne.s	.nobox
	moveq	#32,d2
	moveq	#32,d3
	bsr.w	hitbox
.nobox:
	btst	#0,$F(a6)
	beq.s	.x
	cmpi.w	#48,SPEED(a6)
	bcc.s	.x
	addq.w	#1,SPEED(a6)
.x:
	rts
; Kame_Musi (class $A9) death: drop a gold cube like the Dreamcast's Kame, then
; continue into the sound call this replaced (stack args untouched: tail jump)
kame_drop:
	movem.l	d0-d1/d4,-(a7)
	move.w	X(a6),d0
	move.w	Y(a6),d1
	moveq	#0,d4
	jsr	(EXPLODE).l
	movem.l	(a7)+,d0-d1/d4
	jmp	(SOUND).l
; Big_I (class $91) death: the Dreamcast drops a size-3 gold cube ($8C0C07F2); the
; arcade drops none. Its death sound call at $12425E is replaced by jsr bigi_drop.
bigi_drop:
	movem.l	d0-d1/d4,-(a7)
	move.w	X(a6),d0
	move.w	Y(a6),d1
	moveq	#3,d4
	jsr	(EXPLODE).l
	movem.l	(a7)+,d0-d1/d4
	jmp	(SOUND).l
; Une (class $8E) death: the Dreamcast drops a small cube with a random spread
; ($8C011220, $8C0FB134) and then one on the spot ($8C011208); the arcade only the
; second. Its jsr $3930E at $144774 is replaced by jsr une_drop (d0/d1/d4 are set).
une_drop:
	movem.l	d0-d4/a0-a1,-(a7)
	jsr	(SPREAD).l
	movem.l	(a7)+,d0-d4/a0-a1
	jmp	(EXPLODE).l
; KAITEN2 (class $73, the green 4-armed fighters opening Arrange stage 4) hit: the
; Dreamcast's hit routine ($8C0EC614) also drops a big gold cube (size 2); the
; arcade's ($13D42C) doesn't. Its first instruction is replaced by jsr kaiten_hit.
kaiten_hit:
	bset	#0,$D(a6)			; the instruction this replaced
	movem.l	d0-d1/d4,-(a7)
	move.w	X(a6),d0
	move.w	Y(a6),d1
	moveq	#2,d4
	jsr	(EXPLODE).l
	movem.l	(a7)+,d0-d1/d4
	rts
hb_code_end:

; ---------------------------------------------------------------- descriptors (data)
; arcade layout: name[16], list.w, size.w, init/kill/update/draw/hit, hp.w @+$28, score.l @+$36
	ORG	$17F800		; after the sprite tables ($17F000-$17F7DF)
hb_descs:
hb_desc:
	dc.b	"Hanabi"
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.w	3, $70
	dc.l	hb_init, hb_nop, hb_update, hb_draw, hb_hit
	dc.w	50
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.l	$30
	dc.b	0, 0, 0, 0, 0, 0
cb_desc:
	dc.b	"Chubi"
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.w	3, $76
	dc.l	cb_init, hb_nop, cb_update, cb_draw, cb_hit
	dc.w	50
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.l	$10
	dc.b	0, 0, 0, 0, 0, 0
sb_desc:
	dc.b	"Shobi"
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.w	3, $6E
	dc.l	sb_init, hb_nop, sb_update, sb_draw, sb_hit
	dc.w	10
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.l	$10
	dc.b	0, 0, 0, 0, 0, 0
tp_desc:
	dc.b	"TELPO"
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.w	3, $74
	dc.l	tp_init, tp_kill, tp_update, tp_draw, tp_hit
	dc.w	100
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.l	$30
	dc.b	0, 0, 0, 0, 0, 0
; attack slot (arcade layout, $315EE copies it; from DC $8C1F0B64): flags $86/$80,
; bullet type $340, fire routine, offset (0, -16), aim at the player with angle
; jitter 7, speed $10, timers 1/1/0/0/$3C/$14, aim/tick callbacks, repeat forever
tp_eff:
	dc.b	$86, $80
	dc.w	$0340
	dc.l	tp_fire
	dc.w	0, -16
	dc.b	0, 0, 0, 7, 0, $10, 0, 0
	dc.w	1, 1, 0, 0, $3C, $14
	dc.l	hb_nop, hb_nop
	dc.w	-1
zn_desc:
	dc.b	"Zan"
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.w	3, $74
	dc.l	zn_init, zn_kill, zn_update, zn_draw, zn_hit
	dc.w	100
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.l	$10
	dc.b	0, 0, 0, 0, 0, 0
zz_desc:
	dc.b	"Zz"
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.w	3, $70
	dc.l	zz_init, hb_nop, zz_update, zz_draw, hb_nop
	dc.w	0
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.l	0
	dc.b	0, 0, 0, 0, 0, 0
zc_desc:
	dc.b	"Zc"
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.w	3, $74
	dc.l	zc_init, zn_kill, zc_update, zn_draw, zn_hit
	dc.w	0
	dc.b	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	dc.l	$10
	dc.b	0, 0, 0, 0, 0, 0
; Zan's attack slot (DC $8C1F1810): type $E0, aimed, speed $18, timers 1/1/0/0/$3C/$0A
zn_eff:
	dc.b	$86, $80
	dc.w	$00E0
	dc.l	zn_fire
	dc.w	0, 0
	dc.b	0, 0, 0, 0, 0, $18, 0, 0
	dc.w	1, 1, 0, 0, $3C, $0A
	dc.l	hb_nop, hb_nop
	dc.w	-1
; Zc's attack slot (DC $8C1F183C): type $320 with a flash, aimed, jitter 15,
; speed $18 + random 7, timers 1/1/$14/0/0/0
zc_eff:
	dc.b	$86, $80
	dc.w	$0320
	dc.l	SHOT_FLASH
	dc.w	0, 0
	dc.b	0, 0, 0, $0F, 0, $18, 7, 0
	dc.w	1, 1, $14, 0, 0, 0
	dc.l	hb_nop, hb_nop
	dc.w	-1
hb_descs_end:
