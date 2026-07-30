; CoCo VDG screen and text-formatting routines.
;
; Model code passes token identifiers or zero-terminated strings to this
; module. The two text encodings make seed/context text black-on-green and
; generated text green-on-dark without mixing VDG details into model math.

initialize_training_screen
        ldx     #SCREEN
        lda     #$60
clear_screen
        sta     ,x+
        cmpx    #SCREEN+512
        blo     clear_screen

        ldx     #SCREEN
        lda     #$20
        ldb     #32
fill_title_bar
        sta     ,x+
        decb
        bne     fill_title_bar

        ldx     #SCREEN
        ldu     #message_training
        lbsr    print_string
        ldx     #SCREEN+32
        ldu     #message_epoch
        lbsr    print_black_on_green
        rts

show_training_complete
        ldx     #SCREEN+32
        pshs    x
        lda     #$60
        ldb     #64
clear_training_rows
        sta     ,x+
        decb
        bne     clear_training_rows
        puls    x
        ldu     #message_complete
        lbsr    print_black_on_green
        ldx     #SCREEN+64
        ldu     #message_press_key
        lbsr    print_black_on_green
        rts

show_verification_failed
        ldx     #SCREEN+64
        ldu     #message_verification_failed
        lbsr    print_black_on_green
        rts

; X is a screen destination, U is a zero-terminated ASCII string. CoCo VDG
; text codes are the low six bits of uppercase ASCII.
print_string
        lda     ,u+
        beq     print_string_done
        anda    #$3f
        sta     ,x+
        bra     print_string
print_string_done
        rts

; Print black glyphs on the VDG's green background. ORA maps both uppercase
; ASCII and spaces into the $40-$7F inverse-video character set.
print_black_on_green
        lda     ,u+
        beq     print_black_on_green_done
        ora     #$40
        sta     ,x+
        bra     print_black_on_green
print_black_on_green_done
        rts

; Show the complete two-token context and target on its own 32-column row.
display_training_example
        ldx     #SCREEN+64
        pshs    x
        lda     #$60
        ldb     #32
clear_training_example
        sta     ,x+
        decb
        bne     clear_training_example
        puls    x
        lda     current_context
        lbsr    print_token_id
        ldu     #message_space
        lbsr    print_black_on_green
        lda     current_context+1
        lbsr    print_token_id
        ldu     #message_arrow
        lbsr    print_black_on_green
        lda     current_target
        lbsr    print_token_id_dark
        rts

; Print token A at X and return X immediately after its last character.
print_token_id
        tsta
        bne     print_token_id_text
        ldu     #message_boundary
        lbsr    print_black_on_green
        rts
print_token_id_text
        ldb     #2
        mul
        ldu     #token_pointers
        leau    d,u
        ldu     ,u
        lbsr    print_black_on_green
        rts

; Print token A as green-on-dark generated text at X.
print_token_id_dark
        tsta
        bne     print_token_id_dark_text
        ldu     #message_boundary
        lbsr    print_string
        rts
print_token_id_dark_text
        ldb     #2
        mul
        ldu     #token_pointers
        leau    d,u
        ldu     ,u
        lbsr    print_string
        rts

; Write unsigned A as exactly two decimal VDG characters at X.
write_decimal_2
        clrb
decimal_tens
        cmpa    #10
        blo     decimal_ready
        suba    #10
        incb
        bra     decimal_tens
decimal_ready
        pshs    a
        tfr     b,a
        adda    #$30
        ora     #$40
        sta     ,x+
        puls    a
        adda    #$30
        ora     #$40
        sta     ,x
        rts

message_training
        ifdef   EXPERIMENT_5
        fcc     "COCO LLM EXP-005 TRAINING"
        else
        fcc     "COCO LLM TRAINING"
        endc
        fcb     0
message_epoch
        ifdef   EXPERIMENT_5
        fcc     "EPOCH 00 / 80"
        else
        fcc     "EPOCH 00 / 20"
        endc
        fcb     0
message_arrow
        fcc     " > "
        fcb     0
message_space
        fcc     " "
        fcb     0
message_boundary
        fcc     "#"
        fcb     0
message_seed
        fcc     "# # > "
        fcb     0
message_complete
        fcc     "TRAINING COMPLETE"
        fcb     0
message_press_key
        fcc     "PRESS ANY KEY"
        fcb     0
message_verification_failed
        fcc     "MODEL CHECK FAILED"
        fcb     0
message_generating
        fcc     "GENERATING NAMES"
        fcb     0
message_generated
        fcc     "GENERATION COMPLETE"
        fcb     0
        ifdef   EXPERIMENT_5
message_prompting
        fcc     "COCO LLM PROMPTING"
        fcb     0
message_prompt_help
        fcc     "UP/DOWN SELECT  ENTER GENERATE"
        fcb     0
        endc
