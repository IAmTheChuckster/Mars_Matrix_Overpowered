; Mars Matrix Overpowered: ORIGINAL / ARRANGE mode select on the title screen.
;
; After a coin, the credited title state calls $161952 every frame to print
; "PRESS START" / "CREDIT" (16 bytes at $157F64). That call is replaced with a
; jsr to mm_frame, which reads Up/Down, draws the two menu lines over the
; "OVERPOWERED" text (row $13), then makes the original call.
; The lines are written straight to the 8x8 text layer. Selected line: the gold
; font "CREDIT" uses (tile = $320 + ASCII) with attr $0C; other line: the white
; font (tile = ASCII) with attr $1F.
;
; The stage setup ($14C6A0) took the stage table with
;     lea $14CEEC(pc),a0 / adda.w $FF0BA0.l,a0          (10 bytes at $14C6A6)
; which now calls mm_stage_table: the arcade table for ORIGINAL, the Arrange
; copy (built by overpowered.py / the web patcher at ARR_TABLE) for ARRANGE.
;
; Code is encrypted by overpowered.py; the strings (mm_strings) are data.

	CPU		68000
	PADDING	OFF
	SUPMODE	ON

MENU_ON		:= $FFE902	; word: 1 once the menu has been shown (title_text skips OVERPOWERED)
CREDITS		:= $FF49A3	; byte: credit count
MODE		:= $FFE900	; word: 0 = ORIGINAL, 1 = ARRANGE (RAM is cleared at boot)
V_P1_EDGE	:= $FFB080	; trap15: newly pressed inputs (high word of the held long)
V_P2_EDGE	:= $FFB084
BIT_UP		:= 3
BIT_DOWN	:= 2
CREDIT_PRINT	:= $161952
TXT_VRAM	:= $908000	; 8x8 text layer: col * $80 + row * 4 -> tile.w, attr.w
GOLD_FONT	:= $320		; gold font tile = $320 + ASCII (as "CREDIT")
COL_SEL		:= $0C		; attr of "CREDIT"
COL_OFF		:= $1F		; white
MENU_COL	:= $12
ROW_ORIG	:= $13
ROW_ARR		:= $15
ARC_TABLE	:= $14CEEC
ARR_TABLE	:= $172F20	; Arrange stage table copy (6 x $40), written as data

	ORG	$157F64
mm_hook_title:
	jsr	(mm_frame).l
	nop
	nop
	nop
	nop
	nop
mm_hook_title_end:

	ORG	$14C6A6
mm_hook_stage:
	jsr	(mm_stage_table).l
	nop
	nop
mm_hook_stage_end:

	ORG	$178200
mm_frame:
	movem.l	d0-d4/a0-a1,-(a7)
	move.w	#1,(MENU_ON).l
	tst.b	(CREDITS).l
	bne.s	.menu
	; no credit: OVERPOWERED in gold, no menu
	move.w	#COL_SEL,d3
	move.w	#GOLD_FONT,d4
	moveq	#ROW_ORIG,d2
	lea	(mm_str_op).l,a0
	bsr.w	mm_put
	move.w	#COL_OFF,d3
	moveq	#0,d4
	moveq	#ROW_ARR,d2
	lea	(mm_str_blank).l,a0
	bsr.w	mm_put
	bra.s	.out
.menu:
	move.w	(V_P1_EDGE).l,d0
	or.w	(V_P2_EDGE).l,d0
	btst	#BIT_UP,d0
	beq.s	.noup
	clr.w	(MODE).l
.noup:
	btst	#BIT_DOWN,d0
	beq.s	.nodown
	move.w	#1,(MODE).l
.nodown:
	moveq	#0,d1
	moveq	#ROW_ORIG,d2
	lea	(mm_str_orig).l,a0
	bsr.w	mm_line
	moveq	#1,d1
	moveq	#ROW_ARR,d2
	lea	(mm_str_arr).l,a0
	bsr.w	mm_line
.out:
	movem.l	(a7)+,d0-d4/a0-a1
	; the original call this replaced
	moveq	#1,d0
	pea	(a6)
	movea.l	$10(a6),a6
	jsr	(CREDIT_PRINT).l
	movea.l	(a7)+,a6
	rts

; d1 = line index, d2 = row, a0 = 2 strings of 13 bytes: unselected, selected
mm_line:
	move.w	#COL_OFF,d3
	moveq	#0,d4
	cmp.w	(MODE).l,d1
	bne.s	.go
	move.w	#COL_SEL,d3
	move.w	#GOLD_FONT,d4
	lea	13(a0),a0
.go:
; d2 = row, d3 = attr, d4 = font offset, a0 = string
mm_put:
	lea	(TXT_VRAM+MENU_COL*$80).l,a1
	add.w	d2,d2
	add.w	d2,d2
	adda.w	d2,a1
.ch:
	moveq	#0,d0
	move.b	(a0)+,d0
	beq.s	.done
	add.w	d4,d0
	move.w	d0,(a1)
	move.w	d3,2(a1)
	lea	$80(a1),a1
	bra.s	.ch
.done:
	rts

mm_stage_table:
	clr.w	(MENU_ON).l	; back on the title after the game: show OVERPOWERED again
	lea	(ARC_TABLE).l,a0
	tst.w	(MODE).l
	beq.s	.arcade
	lea	(ARR_TABLE).l,a0
.arcade:
	adda.w	($FF0BA0).l,a0
	rts
mm_code_end:

	ORG	$1783A0
mm_strings:
mm_str_orig:
	dc.b	" ORIGINAL   ",0
	dc.b	">ORIGINAL   ",0
mm_str_arr:
	dc.b	" ARRANGE    ",0
	dc.b	">ARRANGE    ",0
mm_str_op:
	dc.b	" OVERPOWERED",0
mm_str_blank:
	dc.b	"            ",0
	ALIGN	2
mm_strings_end:
