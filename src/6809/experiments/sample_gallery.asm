; EXP-004 presentation: generate a screenful of names from deterministic
; random seeds so the audience can compare what the trained model invents.

show_sample_gallery
        ldx     #SCREEN
        lda     #$60
clear_gallery_screen
        sta     ,x+
        cmpx    #SCREEN+512
        blo     clear_gallery_screen
        ldx     #SCREEN
        lda     #$20
        ldb     #32
fill_gallery_title
        sta     ,x+
        decb
        bne     fill_gallery_title
        ldx     #SCREEN
        ldu     #message_comparison
        lbsr    print_string
        ldx     #SCREEN+32
        ldu     #message_same_seed
        lbsr    print_black_on_green
        ldx     #SCREEN+64
        ldu     #message_before_training
        lbsr    print_black_on_green
        ldx     #untrained_sample_display
        ldu     #SCREEN+96
        ldb     #32
copy_untrained_cell
        lda     ,x+
        sta     ,u+
        decb
        bne     copy_untrained_cell
        ldx     #SCREEN+128
        ldu     #message_after_training
        lbsr    print_black_on_green
        ldd     #sample_seeds
        std     sample_seed_pointer
        ldx     #SCREEN+160
        stx     screen_pointer
        lda     #11
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

        ifdef   DIRECT_TEST
        swi
        else
sample_gallery_finished
        bra     sample_gallery_finished
        endc

sample_seeds
        fdb     6809,6810,6811,6812,6813,6814
        fdb     6815,6816,6817,6818,6819

message_comparison
        fcc     "TRAINING CHANGED THE MODEL"
        fcb     0
message_same_seed
        fcc     "SAME GENERATION SEED 6809"
        fcb     0
message_before_training
        fcc     "BEFORE TRAINING - RANDOM WEIGHTS"
        fcb     0
message_after_training
        fcc     "AFTER TRAINING - LEARNED WEIGHTS"
        fcb     0

untrained_sample_display rmb   32
