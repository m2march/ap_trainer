\version "2.7.40"
\header {
	crossRefNumber = "1                   "
	footnotes = ""
	tagline = "Lily was here 2.18.2 -- automatically converted from ABC"
}
voicedefault =  {
\set Score.defaultBarType = ""

%  tune no 1
 %  meter
 \time 3/4                  \tempo 4=100 %  key
 \key c \major   c''4    c''4   ~    c''4    c''4    \bar "|"   
}

\score{
    <<

	\context Staff="default"
	{
	    \voicedefault 
	}

    >>
	\layout {
	}
	\midi {}
}
