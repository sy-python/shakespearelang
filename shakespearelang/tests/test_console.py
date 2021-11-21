from shakespearelang.repl import start_console
from tatsu.exceptions import FailedParse
from io import StringIO
import pytest
import pexpect

STANDARD_REPL_BEGINNING = """
A REPL-tastic Adventure.

Romeo, a player.
Juliet, a player.

                    Act I: All the World.
                    Scene I: A Stage.

[Enter Romeo and Juliet]

>> """


def test_errors_on_nonsense_characters():
    cli = pexpect.spawn("shakespeare --characters='Foobar,Not Real'")
    expect_output_exactly(
        cli,
        """
A REPL-tastic Adventure.

Foobar, a player.
Not Real, a player.

                    Act I: All the World.
                    Scene I: A Stage.

[Enter Foobar and Not Real]

SPL parse error: failed to parse character
  at line 4
----- context -----

A REPL-tastic Adventure.

∨
Foobar, a player.
∧
Not Real, a player.

                    Act I: All the World.
                    Scene I: A Stage.

----- details -----
parsing stack: character, dramatis_persona, dramatis_personae, play
full error message:
    expecting one of: Achilles Adonis Adriana Aegeon Aemilia Agamemnon Agrippa Ajax Alonso Andromache Angelo Antiochus Antonio Arthur Autolycus Balthazar Banquo Beatrice Benedick Benvolio Bianca Brabantio Brutus Capulet Cassandra Cassius Christopher Cicero Claudio Claudius Cleopatra Cordelia Cornelius Cressida Cymberline Demetrius Desdemona Dionyza Doctor Dogberry Don Donalbain Dorcas Duncan Egeus Emilia Escalus Falstaff Fenton Ferdinand Ford Fortinbras Francisca Friar Gertrude Goneril Hamlet Hecate Hector Helen Helena Hermia Hermonie Hippolyta Horatio Imogen Isabella John Julia Juliet Julius King Lady Lennox Leonato Luciana Lucio Lychorida Lysander Macbeth Macduff Malcolm Mariana Mark Mercutio Miranda Mistress Montague Mopsa Oberon Octavia Octavius Olivia Ophelia Orlando Orsino Othello Page Pantino Paris Pericles Pinch Polonius Pompeius Portia Priam Prince Prospero Proteus Publius Puck Queen Regan Robin Romeo Rosalind Sebastian Shallow Shylock Slender Solinus Stephano Thaisa The Theseus Thurio Timon Titania Titus Troilus Tybalt Ulysses Valentine Venus Vincentio Viola
""",
        eof=True,
    )


def test_works_with_arbitrary_characters():
    cli = pexpect.spawn("shakespeare --characters='Lady Capulet,The Ghost,Horatio'")

    expect_output_exactly(
        cli,
        """
A REPL-tastic Adventure.

Lady Capulet, a player.
The Ghost, a player.
Horatio, a player.

                    Act I: All the World.
                    Scene I: A Stage.

[Enter Lady Capulet, The Ghost and Horatio]

>> """,
    )
    expect_interaction(cli, "[Exeunt]", "Exeunt all")
    expect_interaction(cli, "[Enter Lady Capulet]", "Enter Lady Capulet")
    expect_interaction(cli, "[Enter Horatio]", "Enter Horatio")
    expect_interaction(cli, "exit", "", prompt=False)
    expect_output_exactly(cli, "", eof=True)


def test_runs_noop():
    cli = pexpect.spawn("shakespeare")

    expect_output_exactly(cli, STANDARD_REPL_BEGINNING)
    expect_interaction(cli, "exit", "", prompt=False)
    expect_output_exactly(cli, "", eof=True)


def test_runs_next():
    cli = pexpect.spawn("shakespeare")

    expect_output_exactly(cli, STANDARD_REPL_BEGINNING)
    expect_interaction(cli, "next", "", prompt=False)
    expect_output_exactly(cli, "", eof=True)


def test_runs_continue():
    cli = pexpect.spawn("shakespeare")

    expect_output_exactly(cli, STANDARD_REPL_BEGINNING)
    expect_interaction(cli, "continue", "", prompt=False)
    expect_output_exactly(cli, "", eof=True)


def test_display_parse_error():
    cli = pexpect.spawn("shakespeare")

    expect_output_exactly(cli, STANDARD_REPL_BEGINNING)
    expect_interaction(
        cli,
        "foobar",
        """SPL parse error: failed to parse character
  at line 1
----- context -----
∨
foobar
∧

----- details -----
parsing stack: character, repl_input
full error message:
    expecting one of: Achilles Adonis Adriana Aegeon Aemilia Agamemnon Agrippa Ajax Alonso Andromache Angelo Antiochus Antonio Arthur Autolycus Balthazar Banquo Beatrice Benedick Benvolio Bianca Brabantio Brutus Capulet Cassandra Cassius Christopher Cicero Claudio Claudius Cleopatra Cordelia Cornelius Cressida Cymberline Demetrius Desdemona Dionyza Doctor Dogberry Don Donalbain Dorcas Duncan Egeus Emilia Escalus Falstaff Fenton Ferdinand Ford Fortinbras Francisca Friar Gertrude Goneril Hamlet Hecate Hector Helen Helena Hermia Hermonie Hippolyta Horatio Imogen Isabella John Julia Juliet Julius King Lady Lennox Leonato Luciana Lucio Lychorida Lysander Macbeth Macduff Malcolm Mariana Mark Mercutio Miranda Mistress Montague Mopsa Oberon Octavia Octavius Olivia Ophelia Orlando Orsino Othello Page Pantino Paris Pericles Pinch Polonius Pompeius Portia Priam Prince Prospero Proteus Publius Puck Queen Regan Robin Romeo Rosalind Sebastian Shallow Shylock Slender Solinus Stephano Thaisa The Theseus Thurio Timon Titania Titus Troilus Tybalt Ulysses Valentine Venus Vincentio Viola""",
    )
    expect_interaction(cli, "exit", "", prompt=False)
    expect_output_exactly(cli, "", eof=True)


def test_display_runtime_error():
    cli = pexpect.spawn("shakespeare")

    expect_output_exactly(cli, STANDARD_REPL_BEGINNING)
    expect_interaction(
        cli,
        "Juliet: You are as good as the quotient between a pig and nothing.",
        """SPL runtime error: Cannot divide by zero
  at line 1
----- context -----
Juliet: You are as good as >>the quotient between a pig and nothing<<.

----- state -----
global boolean = False
on stage:
  Romeo = 0 ()
  Juliet = 0 ()
off stage:""",
    )
    expect_interaction(cli, "exit", "", prompt=False)
    expect_output_exactly(cli, "", eof=True)


def test_display_repl_specific_error():
    cli = pexpect.spawn("shakespeare")

    expect_output_exactly(cli, STANDARD_REPL_BEGINNING)
    expect_interaction(cli, "You are as good as nothing.", "Who's saying this?")
    expect_interaction(
        cli,
        "Juliet: Let us proceed to scene II.",
        "Control flow isn't allowed in REPL.",
    )
    expect_interaction(
        cli, "Let us proceed to scene II.", "Control flow isn't allowed in REPL."
    )
    expect_interaction(cli, "exit", "", prompt=False)
    expect_output_exactly(cli, "", eof=True)


def test_last_character_speaking():
    cli = pexpect.spawn("shakespeare")

    expect_output_exactly(cli, STANDARD_REPL_BEGINNING)
    expect_interaction(cli, "Juliet: You are as good as nothing.", "Romeo set to 0")
    expect_interaction(cli, "You are nothing.", "Romeo set to 0")
    expect_interaction(cli, "Romeo: You are nothing.", "Juliet set to 0")
    expect_interaction(cli, "You are nothing.", "Juliet set to 0")
    expect_interaction(cli, "The sum of thyself and a pig", "-1")
    expect_interaction(cli, "Juliet: The sum of thyself and a fat pig", "-2")
    expect_interaction(cli, "exit", "", prompt=False)
    expect_output_exactly(cli, "", eof=True)


def test_detailed_logging():
    cli = pexpect.spawn("shakespeare")

    expect_output_exactly(cli, STANDARD_REPL_BEGINNING)
    cli.sendline(
        "Juliet: You are as good as a good good good good good good animal. Speak your mind! Listen to your heart!"
    )
    expect_output_exactly(
        cli,
        """Juliet: You are as good as a good good good good good good animal. Speak your mind! Listen to your heart!
Romeo set to 64
Outputting Romeo
Outputting character: '@'
Taking input number: """,
    )
    cli.sendline("10")
    expect_output_exactly(cli, "10\nSetting Romeo to input value 10\n>> ")
    expect_interaction(
        cli, "Open your heart!", "Outputting Romeo\nOutputting number: 10"
    )
    expect_interaction(cli, "exit", "", prompt=False)
    expect_output_exactly(cli, "", eof=True)


def test_display_character():
    cli = pexpect.spawn("shakespeare")

    expect_output_exactly(cli, STANDARD_REPL_BEGINNING)
    expect_interaction(cli, "Juliet: Remember thyself! You are a pig! Remember bad Hell! Remember a good animal!", """Romeo pushed 0
Romeo set to -1
Romeo pushed -2
Romeo pushed 2""")
    expect_interaction(cli, "Romeo", "Romeo = -1 (2 -2 0)")
    expect_interaction(cli, "exit", "", prompt=False)
    expect_output_exactly(cli, "", eof=True)


def test_display_state():
    cli = pexpect.spawn("shakespeare")

    expect_output_exactly(cli, STANDARD_REPL_BEGINNING)
    expect_interaction(cli, "Juliet: Remember thyself! You are a pig!", "Romeo pushed 0\nRomeo set to -1")
    expect_interaction(cli, "state", """global boolean = False
on stage:
  Romeo = -1 (0)
  Juliet = 0 ()
off stage:""")
    expect_interaction(cli, "exit", "", prompt=False)
    expect_output_exactly(cli, "", eof=True)


def expect_interaction(cli, to_send, to_receive, prompt=True):
    cli.sendline(to_send)
    full_output = to_send + "\n"
    if to_receive:
        full_output = full_output + to_receive + "\n"
    if prompt:
        full_output = full_output + ">> "
    expect_output_exactly(cli, full_output)


def expect_output_exactly(cli, output, eof=False):
    try:
        cli.expect_exact(output.replace("\n", "\r\n").encode("UTF-8"), timeout=0.5)
    except pexpect.exceptions.TIMEOUT:
        assert cli.before.decode("UTF-8") == output.replace("\n", "\r\n")
    assert cli.before.decode("UTF-8") == ""

    if eof:
        cli.expect(pexpect.EOF, timeout=0.5)
        assert cli.before.decode("UTF-8") == ""
