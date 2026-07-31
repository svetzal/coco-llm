; Direct-simulator interaction test for the EXP-007 sentence workbench.

DIRECT_TEST  equ     1
EXP7_UI_TEST equ     1

        org     $2000

        include "../experiments/experiment_007.asm"

exp7_ui_test_start
        clr     exp7_ui_stage
        lbsr    completion_policy_initialize
        lbsr    completion_initialize_screen

        ; The shared screen is bound to EXP-007's measured model shape.
        ldd     COMPLETION_SCREEN+480
        cmpd    #$7274                 ; normal-field "24"
        lbne    exp7_ui_test_failed
        lda     COMPLETION_SCREEN+482
        cmpa    #$73                   ; normal-field "3"
        lbne    exp7_ui_test_failed
        inc     exp7_ui_stage

        ; A completed sentence recreates the exported five-token test vector.
        ; <END> is token zero, ranks first, and is visibly rendered rather than
        ; being confused with the old "no suggestion" sentinel.
        ldx     #exp7_ui_test_phrase
        ldu     #completion_input_buffer
        ldb     #16
        stb     completion_input_length
exp7_ui_copy_phrase
        lda     ,x+
        sta     ,u+
        decb
        bne     exp7_ui_copy_phrase
        clr     ,u
        lbsr    completion_policy_predict_input
        lda     exp7_top_one_token
        cmpa    exp7_expected_top_three
        lbne    exp7_ui_test_failed
        lda     exp7_top_two_token
        cmpa    exp7_expected_top_three+1
        lbne    exp7_ui_test_failed
        lda     exp7_top_three_token
        cmpa    exp7_expected_top_three+2
        lbne    exp7_ui_test_failed
        lda     completion_suggestion_count
        cmpa    #3
        lbne    exp7_ui_test_failed
        tst     completion_suggestions_visible
        lbeq    exp7_ui_test_failed
        ldx     completion_popover_origin
        leax    2,x
        ldd     ,x
        cmpd    #$3c05                 ; reverse-field "<E"
        lbne    exp7_ui_test_failed
        clr     completion_selected_suggestion
        lbsr    completion_policy_apply_suggestion
        lda     completion_input_length
        cmpa    #16
        lbne    exp7_ui_test_failed
        ldd     COMPLETION_STATUS_SCREEN
        cmpd    #$454e                 ; normal-field "EN"
        lbne    exp7_ui_test_failed
        inc     exp7_ui_stage

        ; Attached punctuation is tokenized independently and occupies the
        ; newest context position rather than becoming part of DATA.
        ldx     #exp7_ui_punctuation_phrase
        ldu     #completion_input_buffer
        ldb     #13
        stb     completion_input_length
exp7_ui_copy_punctuation
        lda     ,x+
        sta     ,u+
        decb
        bne     exp7_ui_copy_punctuation
        clr     ,u
        lbsr    exp7_parse_input
        lbcs    exp7_ui_test_failed
        lda     exp7_current_context+4
        cmpa    #EXP7_TOKEN_COLON
        lbne    exp7_ui_test_failed
        tst     exp7_prefix_length
        lbne    exp7_ui_test_failed
        inc     exp7_ui_stage

        ; Typing punctuation removes a pending model-supplied separator.
        ldx     #exp7_ui_model_space
        ldu     #completion_input_buffer
        ldb     #6
        stb     completion_input_length
exp7_ui_copy_model_space
        lda     ,x+
        sta     ,u+
        decb
        bne     exp7_ui_copy_model_space
        clr     ,u
        lda     #$2e
        lbsr    completion_policy_append_typed_character
        lbcs    exp7_ui_test_failed
        lda     completion_input_length
        cmpa    #6
        lbne    exp7_ui_test_failed
        ldd     completion_input_buffer+4
        cmpd    #$4c2e                 ; "L."
        lbne    exp7_ui_test_failed
        inc     exp7_ui_stage

        ; Accepting a punctuation suggestion also attaches it, then leaves one
        ; separator ready for the next word.
        ldx     #exp7_ui_model_space
        ldu     #completion_input_buffer
        ldb     #6
        stb     completion_input_length
exp7_ui_restore_model_space
        lda     ,x+
        sta     ,u+
        decb
        bne     exp7_ui_restore_model_space
        clr     ,u
        lda     #EXP7_TOKEN_PERIOD
        sta     exp7_top_one_token
        clr     completion_selected_suggestion
        clr     exp7_prefix_length
        lda     #1
        sta     completion_suggestions_visible
        lbsr    completion_policy_apply_suggestion
        lda     completion_input_length
        cmpa    #7
        lbne    exp7_ui_test_failed
        ldd     completion_input_buffer+5
        cmpd    #$2e20                 ; ". "
        lbne    exp7_ui_test_failed
        inc     exp7_ui_stage

        ; Restore the exported fixed vector for shared runner validation.
        ldx     #exp7_test_context
        ldu     #exp7_current_context
        ldd     ,x++
        std     ,u++
        ldd     ,x++
        std     ,u++
        lda     ,x
        sta     ,u
        clr     exp7_prefix_length
        ldd     #EXP7_MODEL_BASE
        std     exp7_position_base
        lbsr    exp7_predict_top_three

        lda     #1
        sta     exp7_parity_result
        swi
exp7_ui_test_failed
        clr     exp7_parity_result
        swi

exp7_ui_test_phrase
        fcc     "RUN THE PROGRAM."
exp7_ui_punctuation_phrase
        fcc     "BETTER DATA: "
exp7_ui_model_space
        fcc     "MODEL "

exp7_parity_result
        rmb     1
exp7_ui_stage
        rmb     1
