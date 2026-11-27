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
	move.w	#TITLE_ROW,-(a7)
	move.w	#TITLE_COL,-(a7)
	jsr	(TXT_CURSOR).l
	pea	(tt_string).l
	jsr	(TXT_PRINT).l
	addq.w	#8,a7
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
