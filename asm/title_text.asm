; Mars Matrix Overpowered: "OVERPOWERED" on the title screen, under the logo.
;
; The title screen prints its copyright lines with:
;     move.w #row,-(a7) / move.w #col,-(a7) / jsr $152232   ; set text cursor
;     pea string(pc)    / jsr $152446 / addq.w #8,a7         ; print (NUL-terminated)
; Japan: rows $17-$19 at column 9 (strings $158528...), USA/Asia: rows $16-$19.
; Both paths continue at $1580AE: move.w #$1F,-(a7) / jsr $152228 (10 bytes),
; which is hooked here.
;
; Code goes in free ROM after bullet_cancel ($178000-$1780C5) and is encrypted
; by overpowered.py; the string is data and is written unencrypted.

	CPU		68000
	PADDING	OFF
	SUPMODE	ON

TXT_CURSOR	:= $152232	; (col.w, row.w on stack) set text cursor
TXT_PRINT	:= $152446	; (string.l on stack) print NUL-terminated string
HOOK		:= $1580AE
HOOK_CONT	:= $1580B8	; after the two replaced instructions
ORIG_FUNC	:= $152228

TXT_VRAM	:= $908000	; 8x8 text layer: col * $80 + row * 4 -> tile.w, attr.w
GOLD_FONT	:= $320		; gold font tile = $320 + ASCII (as "CREDIT")
COL_GOLD	:= $0C		; attr of "CREDIT"
TITLE_ROW	:= $13		; text row (8 px), just under the logo
TITLE_COL	:= $13		; 9 + (31 - 11) / 2: centered on the copyright lines

	ORG	HOOK
tt_hook:
	jmp	(tt_title_text).l
	nop
	nop
tt_hook_end:

	ORG	$178100
tt_title_text:
	; OVERPOWERED in the gold CREDIT font, written straight to the text layer
	; (the menu, once a coin is in, redraws its two lines over these rows every frame)
	movem.l	d0/a0-a1,-(a7)
	lea	(TXT_VRAM+TITLE_COL*$80+TITLE_ROW*4).l,a1
	lea	(tt_string).l,a0
.ch:
	moveq	#0,d0
	move.b	(a0)+,d0
	beq.s	.blank
	addi.w	#GOLD_FONT,d0
	move.w	d0,(a1)
	move.w	#COL_GOLD,2(a1)
	lea	$80(a1),a1
	bra.s	.ch
.blank:
	; clear the ARRANGE line left over from the credited menu
	lea	(TXT_VRAM+(TITLE_COL-1)*$80+(TITLE_ROW+2)*4).l,a1
	moveq	#11,d0
.bl:
	move.w	#$20,(a1)
	move.w	#$1F,2(a1)
	lea	$80(a1),a1
	dbra	d0,.bl
	movem.l	(a7)+,d0/a0-a1
.skip:
	; the two instructions the hook replaced
	move.w	#$1F,-(a7)
	jsr	(ORIG_FUNC).l
	jmp	(HOOK_CONT).l
tt_code_end:

	ORG	$178180
tt_string:
	dc.b	"OVERPOWERED",0
	ALIGN	2
tt_string_end:
