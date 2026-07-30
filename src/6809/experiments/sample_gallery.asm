; EXP-004 presentation: generate a screenful of names from deterministic
; random seeds so the audience can compare what the trained model invents.

show_sample_gallery
        ldx     #SCREEN+64
        lda     #$60
        ldb     #32
clear_key_prompt
        sta     ,x+
        decb
        bne     clear_key_prompt
        ldx     #SCREEN+96
        ldu     #message_generating
        lbsr    print_black_on_green
        ldd     #sample_seeds
        std     sample_seed_pointer
        ldx     #SCREEN+128
        stx     screen_pointer
        lda     #12
        sta     sample_count
sample_loop
        ldx     sample_seed_pointer
        ldd     ,x++
        stx     sample_seed_pointer
        std     rng_state
        lbsr    generate_name
        ldd     screen_pointer
        addd    #32
        std     screen_pointer
        dec     sample_count
        bne     sample_loop

        ldx     #SCREEN+96
        ldu     #message_generated
        lbsr    print_black_on_green
        ifdef   DIRECT_TEST
        swi
        else
sample_gallery_finished
        bra     sample_gallery_finished
        endc

sample_seeds
        fdb     6809,6810,6811,6812,6813,6814
        fdb     6815,6816,6817,6818,6819,6820
