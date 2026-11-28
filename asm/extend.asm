; Mars Matrix Overpowered: an extra life every 10,000,000,000 points.
;
; Scores are 12-digit BCD (6 bytes, max 999999999990). Every score add goes through
; $321B4: a0 = amount, a1 = score (both 6 bytes), d0/a0/a1 preserved. Its first
; 6 bytes (movem.l d0/a0-a1,-(a7) / addq.w #6,a0) are replaced by a jmp to ex_add,
; which does the same add and then compares the score's top byte (the digits worth
; 10,000,000,000 and 100,000,000,000) before and after. For each step crossed, the
; player's lives (the word just before the score) go up by one, up to 5.
; Game struct ($FF4978): P1 lives +$30, score +$32; P2 lives +$56, score +$58.
;
; Code is encrypted by overpowered.py.

	CPU		68000
	PADDING	OFF
	SUPMODE	ON

SCORE_ADD	:= $0321B4
P1_SCORE	:= $FF49AA
P2_SCORE	:= $FF49D0
MAX_LIVES	:= 5

	ORG	SCORE_ADD
ex_hook:
	jmp	(ex_add).l
ex_hook_end:

	ORG	$17CF00
ex_add:
	movem.l	d0-d2/a0-a1,-(a7)
	moveq	#0,d1
	move.b	(a1),d1			; top BCD byte before
	; the original add (with its 999999999990 cap)
	addq.w	#6,a0
	addq.w	#6,a1
	sub.w	d0,d0
	abcd	-(a0),-(a1)
	abcd	-(a0),-(a1)
	abcd	-(a0),-(a1)
	abcd	-(a0),-(a1)
	abcd	-(a0),-(a1)
	abcd	-(a0),-(a1)
	bcc.s	.nocap
	move.l	#$99999999,(a1)
	move.w	#$9990,4(a1)
.nocap:
	; a1 = score again (compare 24 bits: RAM is also reached as $FFxxxx)
	move.l	a1,d0
	andi.l	#$FFFFFF,d0
	cmpi.l	#P1_SCORE,d0
	beq.s	.player
	cmpi.l	#P2_SCORE,d0
	bne.s	.done
.player:
	moveq	#0,d0
	move.b	(a1),d0			; top BCD byte after
	bsr.s	ex_bin
	exg	d0,d1
	bsr.s	ex_bin			; d0 = old, d1 = new (binary)
	sub.w	d0,d1
	ble.s	.done
	move.w	-2(a1),d0
	cmpi.w	#MAX_LIVES,d0
	bhs.s	.done			; already at the cap (or above it): no change
	add.w	d0,d1
	cmpi.w	#MAX_LIVES,d1
	bls.s	.set
	moveq	#MAX_LIVES,d1
.set:
	move.w	d1,-2(a1)
.done:
	movem.l	(a7)+,d0-d2/a0-a1
	rts

; d0.b BCD -> d0.w binary (d2 scratch)
ex_bin:
	move.w	d0,d2
	andi.w	#$0F,d2
	lsr.w	#4,d0
	mulu	#10,d0
	add.w	d2,d0
	rts
ex_code_end:
