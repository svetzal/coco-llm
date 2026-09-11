"""Compare the 6809 signed-multiply kernels against their 6309 MULD replacements.

Cycle counts are datasheet arithmetic, not a measurement. Each instruction
carries its addressing mode so the table can be audited line by line against
the MC6809E data sheet and the HD63B09EP technical reference. The 6809 side is
transcribed from the kernels in `src/6809/model_forward.asm`; the operand
addresses live above the direct page, so every variable access is extended.

The only measurement here is CALLS_PER_TRAINING_RUN, read out of the direct
simulator with a temporary 24-bit counter at the head of multiply_s8_s16.
"""

# (mnemonic, addressing mode, 6809 cycles, 6309 native cycles)
M6809_S8_S16 = [
    ("sta  multiply_factor", "extended", 5),
    ("ldb  1,x", "indexed 5-bit", 5),
    ("mul", "inherent", 11),
    ("std  multiply_product", "extended", 6),
    ("lda  multiply_factor", "extended", 5),
    ("ldb  ,x", "indexed no-offset", 4),
    ("mul", "inherent", 11),
    ("addb multiply_product", "extended", 5),
    ("stb  multiply_product", "extended", 5),
    ("tst  multiply_factor", "extended", 7),
    ("bpl  multiply_ready", "relative", 3),
    ("lda  multiply_product", "extended", 5),  # sign-fix, negative path only
    ("suba 1,x", "indexed 5-bit", 5),  # sign-fix
    ("sta  multiply_product", "extended", 5),  # sign-fix
    ("ldd  multiply_product", "extended", 6),
    ("rts", "inherent", 5),
]
SIGN_FIX = slice(11, 14)

M6809_S16_S16 = [
    ("std  multiply_factor16", "extended", 6),
    ("lda  multiply_factor16+1", "extended", 5),
    ("ldb  1,x", "indexed 5-bit", 5),
    ("mul", "inherent", 11),
    ("std  multiply_product", "extended", 6),
    ("lda  multiply_factor16", "extended", 5),
    ("ldb  1,x", "indexed 5-bit", 5),
    ("mul", "inherent", 11),
    ("addb multiply_product", "extended", 5),
    ("stb  multiply_product", "extended", 5),
    ("lda  multiply_factor16+1", "extended", 5),
    ("ldb  ,x", "indexed no-offset", 4),
    ("mul", "inherent", 11),
    ("addb multiply_product", "extended", 5),
    ("stb  multiply_product", "extended", 5),
    ("ldd  multiply_product", "extended", 6),
    ("rts", "inherent", 5),
]

# 6309 native mode. MULD indexed is 30 cycles plus the indexed postbyte cost,
# which is zero for ",x". SEX is 1 in native mode, TFR is 4, RTS is 4.
M6309_S8_S16 = [
    # The loop hands the multiplicand over in A, as the engine's own forward
    # pass does, so the port pays for moving it rather than the benchmark
    # changing its loop to flatter the newer chip.
    ("tfr  a,b", "immediate", 4),
    ("sex", "inherent", 1),
    ("muld ,x", "indexed no-offset", 30),
    ("tfr  w,d", "immediate", 4),
    ("rts", "inherent", 4),
]
M6309_S16_S16 = [
    ("muld ,x", "indexed no-offset", 30),
    ("tfr  w,d", "immediate", 4),
    ("rts", "inherent", 4),
]

# lbsr into the named experiment policy, then lbra into the kernel.
CALL_OVERHEAD_6809 = 9 + 5
CALL_OVERHEAD_6309 = 8 + 4

# Measured: temporary 24-bit counter at the head of multiply_s8_s16, read back
# from $304A after `make model-test`. Counter held $04AD9C.
CALLS_PER_TRAINING_RUN = 0x04AD9C

# The project's recorded EXP-004 figures, the live training run.
BASELINE_INSTRUCTIONS = 16_368_255
BASELINE_CYCLES = 66_700_000  # cycle-model projection recorded in EXP-004


def total(listing):
    return sum(cycles for _, _, cycles in listing)


def report():
    neg = total(M6809_S8_S16)
    pos = neg - total(M6809_S8_S16[SIGN_FIX])
    avg8 = (neg + pos) / 2
    new8 = total(M6309_S8_S16)

    old16 = total(M6809_S16_S16)
    new16 = total(M6309_S16_S16)

    print("8-bit by 16-bit signed multiply (EXP-004, the live training run)")
    print(
        f"  6809  negative operand   {neg:3d} cycles, {len(M6809_S8_S16)} instructions"
    )
    print(
        f"  6809  positive operand   {pos:3d} cycles, {len(M6809_S8_S16) - 3} instructions"
    )
    print(
        f"  6309  either sign        {new8:3d} cycles, {len(M6309_S8_S16)} instructions"
    )
    print(f"  kernel speedup           {avg8 / new8:.2f}x on the average operand")
    print(
        f"  the sign fix             {total(M6809_S8_S16[SIGN_FIX])} cycles on the 6809, "
        "and no instruction at all on the 6309"
    )
    print()
    print("16-bit by 16-bit signed multiply (EXP-005, the prompted completions)")
    print(
        f"  6809                     {old16:3d} cycles, {len(M6809_S16_S16)} instructions"
    )
    print(
        f"  6309                     {new16:3d} cycles, {len(M6309_S16_S16)} instructions"
    )
    print(f"  kernel speedup           {old16 / new16:.2f}x")
    print()

    old_call = avg8 + CALL_OVERHEAD_6809
    new_call = new8 + CALL_OVERHEAD_6309
    spent = CALLS_PER_TRAINING_RUN * old_call
    saved = CALLS_PER_TRAINING_RUN * (old_call - new_call)

    print("Whole training run. PROJECTION, not a measurement.")
    print(f"  measured calls           {CALLS_PER_TRAINING_RUN:,}")
    print(
        f"  cycles in the kernel     {spent / 1e6:.1f}M of {BASELINE_CYCLES / 1e6:.1f}M "
        f"({spent / BASELINE_CYCLES:.0%} of the run)"
    )
    print(f"  cycles saved by MULD     {saved / 1e6:.1f}M")
    print(
        f"  speedup from MULD alone  {BASELINE_CYCLES / (BASELINE_CYCLES - saved):.2f}x"
    )
    print(
        f"  with the 2x clock        {2 * BASELINE_CYCLES / (BASELINE_CYCLES - saved):.2f}x "
        "against a stock CoCo 1"
    )
    print()
    print("  Native mode also removes a cycle or two from most of the other")
    print("  instructions in the run. That is deliberately excluded here. The")
    print("  real figure comes off a stopwatch on the physical CoCo 3.")
    print()
    compare_against_measurement(avg8, new8)


# What XRoar measured, in cycles per multiplication, from
# `make bench-xroar-6309`: 58,000 multiplications, 200 passes over the trained
# parameter block, ticks converted at 60 Hz and 0.895 MHz.
MEASURED_6809_MODE = 134.0
MEASURED_NATIVE_MODE = 116.2
MEASURED_MULD = 87.4

# The benchmark loop around each kernel call, from the same data sheet.
BENCH_LOOP = [
    ("lda  ,u+", "indexed auto-increment", 6),
    ("jsr  ,y", "indexed no-offset", 7),
    ("addd bench_sum", "extended", 7),
    ("std  bench_sum", "extended", 6),
    ("leax 2,x", "indexed 5-bit", 5),
    ("ldd  bench_items_left", "extended", 6),
    ("subd #1", "immediate", 4),
    ("std  bench_items_left", "extended", 6),
    ("bne  bench_item", "relative", 3),
]


def compare_against_measurement(avg8: float, new8: int) -> None:
    """The data sheet is only worth anything if the machine agrees with it.

    Only the first row is a clean prediction: every cycle in it is tabulated,
    nothing is fitted, and it is checked against a measurement taken later.
    The other two rows need native-mode timings for the loop, which are not
    transcribed here, so they are reported as what the measurement implies
    about the kernel rather than as predictions of it.
    """
    loop = total(BENCH_LOOP)
    predicted = avg8 + loop
    error = (predicted - MEASURED_6809_MODE) / MEASURED_6809_MODE
    print("Data sheet against XRoar, cycles per multiplication")
    print(
        f"  6809 kernel, 6809 mode     kernel {avg8:.1f} + loop {loop} "
        f"= {predicted:.1f}"
    )
    print(
        f"                             measured {MEASURED_6809_MODE:.1f}, "
        f"{error:+.1%}. Nothing fitted."
    )
    print()
    print("  What the other two rows imply, given that loop:")
    print(
        f"  6809 kernel, native mode   {MEASURED_NATIVE_MODE:.1f} measured, "
        f"so kernel and loop together save "
        f"{MEASURED_6809_MODE - MEASURED_NATIVE_MODE:.1f}"
    )
    print(
        f"  MULD kernel, native mode   {MEASURED_MULD:.1f} measured, and the "
        f"data sheet kernel is {new8}, leaving "
        f"{MEASURED_MULD - new8:.1f} for the loop"
    )
    print(
        f"                             against {loop} in 6809 mode, which is "
        "the native-mode saving"
    )
    print()
    print("  XRoar calls its own 6309 emulation UNVERIFIED, so the last two")
    print("  rows are corroboration rather than proof. The physical CoCo 3 is")
    print("  the authority for anything the 6309 does.")


def prove_bit_exact():
    """The 6809 kernel already yields the low word of the true signed product,
    which is exactly what MULD leaves in W. Check every input pair."""

    def kernel(a_signed, x_signed):
        a, x = a_signed & 0xFF, x_signed & 0xFFFF
        xhi, xlo = x >> 8, x & 0xFF
        prod = a * xlo
        hi, lo = (prod >> 8) & 0xFF, prod & 0xFF
        hi = (hi + ((a * xhi) & 0xFF)) & 0xFF
        if a_signed < 0:
            hi = (hi - xlo) & 0xFF
        return (hi << 8) | lo

    cases = 0
    for a in range(-128, 128):
        for x in range(-32768, 32768):
            assert kernel(a, x) == ((a * x) & 0xFFFF), (a, x)
            cases += 1
    print(f"Bit-exactness: {cases:,} input pairs, every one identical.")
    print("A MULD kernel taking the low word of Q cannot diverge from the")
    print("engine the CoCo 1 runs. The contract in AGENTS.md holds.")


if __name__ == "__main__":
    report()
    print()
    prove_bit_exact()
