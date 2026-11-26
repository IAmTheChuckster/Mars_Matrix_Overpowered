; Mars Matrix Overpowered: chain bullet cancelling into cubes.
;
; When an enemy is killed, every enemy bullet within CANCEL_R_ENEMY pixels of it
; is removed and replaced with a small gold cube. Every bullet within
; CANCEL_R_CHAIN pixels of a cancelled bullet is cancelled too, chaining outward.
;
; Assembled by overpowered.py with trap15's bundled AS (asw), then encrypted.
; All addresses are 68000 addresses in the decrypted program.

	CPU		68000
	PADDING	OFF
	SUPMODE	ON

; ---- game addresses -------------------------------------------------------
ENEMY_KILLED	:= $03222A	; enemy killed: adds score/EXP, a6 = enemy (x $12, y $16)
ENEMY_KILLED_CONT := $032232	; after its first two instructions
NODE_FREE	:= $031C80	; free list node (node pointer on stack), keeps all but d0
CUBE_SPAWN	:= $03930E	; spawn cube: d0 x, d1 y, d4 type; falls straight down
BUL_HEAD	:= $FF000C	; enemy bullet list: pointer to sentinel node
BUL_COUNT	:= $FF0010	; enemy bullet count (word)
; bullet node ($22 bytes): +0 next, +4 prev, +8 x (word), +$C y (word),
; +$10/+$14 velocity. Drawn/moved by $32D6C, which deletes bullets that leave
; the screen, so every bullet in this list is on screen.
; (Build 4 used $FF0056/$FF005A by mistake: that list is player shots /
; effects, not enemy bullets.)

; ---- settings -------------------------------------------------------------
CANCEL_R_ENEMY	:= 24		; pixels around the killed enemy
CANCEL_R_CHAIN	:= 16		; pixels around each cancelled bullet
CUBE_TYPE	:= 1		; small gold cube (what most enemies drop)
CANCEL_BUF	:= $FFE000	; queue of cancelled bullet positions (unused RAM)
CANCEL_MAX	:= 512		; queue entries (4 bytes each)

CODE_BASE	:= $178000	; free (zero-filled) ROM before trap15's code at $17FE00

; ---- hook -----------------------------------------------------------------
; Original: movem.l d0-d1,-(a7) / move.l $60(a6),d0  (8 bytes)
	ORG	ENEMY_KILLED
bc_hook:
	jmp	(bc_enemy_killed).l
	nop
bc_hook_end:

; ---- routine --------------------------------------------------------------
	ORG	CODE_BASE
bc_enemy_killed:
	movem.l	d0-d7/a0-a5,-(sp)
	move.w	$12(a6),d0
	move.w	$16(a6),d1
	lea	(CANCEL_BUF).l,a3	; a3 = queue write pointer
	movea.l	a3,a2			; a2 = queue read pointer
	moveq	#CANCEL_R_ENEMY,d7
	bsr.w	bc_cancel_around
.chain:
	cmpa.l	a3,a2
	beq.s	.done
	move.w	(a2)+,d0
	move.w	(a2)+,d1
	moveq	#CANCEL_R_CHAIN,d7
	bsr.w	bc_cancel_around
	bra.s	.chain
.done:
	movem.l	(sp)+,d0-d7/a0-a5
	; the two instructions the hook replaced
	movem.l	d0-d1,-(sp)
	move.l	$60(a6),d0
	jmp	(ENEMY_KILLED_CONT).l

; Cancel every bullet strictly within d7 pixels of (d0,d1).
; Pushes each cancelled bullet's position to the queue at a3.
; Uses d2-d6, a0, a1, a4, a5.
bc_cancel_around:
	move.w	d7,d6
	mulu.w	d6,d6			; r^2
	movea.l	(BUL_HEAD).l,a0		; sentinel
	movea.l	(a0),a1			; first bullet
.next:
	cmpa.l	a0,a1
	beq.w	.end
	move.w	8(a1),d2
	sub.w	d0,d2
	bpl.s	.dxpos
	neg.w	d2
.dxpos:
	cmp.w	d7,d2
	bcc.s	.skip
	move.w	$C(a1),d3
	sub.w	d1,d3
	bpl.s	.dypos
	neg.w	d3
.dypos:
	cmp.w	d7,d3
	bcc.s	.skip
	mulu.w	d2,d2
	mulu.w	d3,d3
	add.l	d3,d2
	cmp.l	d6,d2
	bcc.s	.skip
	; --- cancel this bullet ---
	move.w	8(a1),d4		; position
	move.w	$C(a1),d5
	movea.l	(a1),a4			; next
	movea.l	4(a1),a5		; prev
	move.l	a5,4(a4)		; unlink
	move.l	a4,(a5)
	move.l	a1,-(sp)
	jsr	(NODE_FREE).l
	addq.w	#4,sp
	subq.w	#1,(BUL_COUNT).l
	cmpa.l	#CANCEL_BUF+CANCEL_MAX*4,a3
	bcc.s	.full
	move.w	d4,(a3)+
	move.w	d5,(a3)+
.full:
	movem.l	d0-d1,-(sp)
	move.w	d4,d0
	move.w	d5,d1
	moveq	#CUBE_TYPE,d4
	jsr	(CUBE_SPAWN).l
	movem.l	(sp)+,d0-d1
	movea.l	a4,a1
	bra.w	.next
.skip:
	movea.l	(a1),a1
	bra.w	.next
.end:
	rts
bc_end:
