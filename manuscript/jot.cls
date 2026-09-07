\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{jot}
              [2026/07/29 v1.3
Non standard LaTeX document class]

\newif\if@debug
\@debugfalse
\newif\ifpdfmode\pdfmodefalse

\ifx\pdfoutput\undefined
 \else
 \ifnum\the\pdfoutput > 0
     \pdfmodetrue
  \fi
\fi
\newcommand\@ptsize{}
\newif\if@restonecol
\newif\if@titlepage
\@titlepagefalse
   \setlength\paperheight {297mm}%
    \setlength\paperwidth  {210mm}%
    \ifpdfmode
        \pdfpagewidth=210mm
        \pdfpageheight=297mm
    \else
	\special{papersize=210mm,297mm}%
   \fi
\def\@ptsize{0}
\DeclareOption{ela}{\@debugtrue}
\DeclareOption{twocolumn}{\@twocolumntrue}
\DeclareOption{twoside}{\@twosidetrue  \@mparswitchtrue}
\def\nameofgame{Journal of Telecommunications\par and Information Technology}
\def\@nameofgame{Journal of Telecommunications and Information Technology}
\ExecuteOptions{10pt,twocolumn,twoside}
%
\newcount\@firstpage
\newcount\@lastpage
\def\Volnum#1{\gdef\@volnum{#1}}
\def\Num#1{\gdef\@numnum{#1}}
\def\Year#1{\gdef\@Year{#1}}
\def\Title#1{\gdef\@title{#1}}
\def\Keywords#1{\gdef\@nkeywords{#1}}
\def\FirstPage#1{\@firstpage=#1}
\FirstPage{0}

\font\switzx=qx-qhvbi at 7pt
\font\switzy=qx-qhvr at 7pt
\def\switz{\switzx}
\def\swity{\switzy}

\def\doi#1{%
    \gdef\@doi{#1}%
    \bgroup
	\def\url##1{##1}%
	\xdef\@@doi{#1}%
    \egroup}

\doi{}
\Year{0}
\Volnum{0}
\Num{0}
\newlength\abovecaptionskip
\newlength\belowcaptionskip

\ProcessOptions
\input{size1\@ptsize.clo}

\def\@xvipt{16}
\def\@xxiipt{22}
\def\@xxpt{20}
\def\@xxvpt{24.8}
\def\@ixpt{9}
\def\@xivpt{14.35}
\if@debug
    \def\xLarge{\@setfontsize\xLarge\@xxvpt{29.8}}
    \def\Large{\@setfontsize\Large\@xivpt{25}}%!
    \def\large{\@setfontsize\large\@xiipt{20}}%!
    \def\xlarge{\@setfontsize\xlarge\@xvipt{20}}%!
    \def\ysmall{\@setfontsize\ysmall\@ixpt{15}%
     \abovedisplayskip 7\p@ \@plus 1\p@ \@minus 0.5\p@
     \abovedisplayshortskip 2\p@ \@plus 0.2\p@ minus 0.2pt
     \belowdisplayshortskip 2\p@ \@plus 0.2\p@ minus 0.2pt
     \belowdisplayskip \abovedisplayskip
    }%!
    \def\esmall{\@setfontsize\small\@xipt{19}%
     \abovedisplayskip 7\p@ \@plus 1\p@ \@minus 0.5\p@
     \abovedisplayshortskip 2\p@ \@plus 0.2\p@ minus 0.2pt
     \belowdisplayshortskip 2\p@ \@plus 0.2\p@ minus 0.2pt
     \belowdisplayskip \abovedisplayskip
    }%!
    \def\small{\@setfontsize\small\@xipt{15}%
     \abovedisplayskip 5\p@ \@plus 1\p@ \@minus 0.5\p@
     \abovedisplayshortskip 1\p@ \@plus 0.2\p@ minus 0.2pt
     \belowdisplayshortskip 1\p@ \@plus 0.2\p@ minus 0.2pt
     \belowdisplayskip \abovedisplayskip
    }%!
    \def\normalsize{%
       \@setfontsize\normalsize\@xiipt{19.0}%
       \abovedisplayskip 7\p@ \@plus 1\p@ \@minus 0.5\p@
       \abovedisplayshortskip 2\p@ \@plus 0.2\p@ minus 0.2pt
       \belowdisplayshortskip 2\p@ \@plus 0.2\p@ minus 0.2pt
       \belowdisplayskip \abovedisplayskip
       }

    \def\@listi{\leftmargin\leftmargini
		\parsep 0\p@ \@plus 0.1\p@ \@minus 0.1\p@
		\topsep 0\p@ \@plus 0.1\p@ \@minus  0.1\p@
		\itemsep0\p@ \@plus 0.1\p@ \@minus 0.1\p@}
    \let\@listI\@listi
    \@listi
    \def\@listii {\leftmargin\leftmarginii
		  \labelwidth\leftmarginii
		  \advance\labelwidth-\labelsep
		  \topsep    0\p@ \@plus 0.1\p@ \@minus 0.1\p@
		  \parsep    0\p@ \@plus 0.1\p@  \@minus 0.1\p@
		  \itemsep   0pt}
\else
    \def\xLarge{\@setfontsize\xLarge\@xxvpt{29.8}}
    \def\Large{\@setfontsize\Large\@xiipt{14}}%!
    \def\large{\@setfontsize\large\@xipt{12}}%!
    \def\xlarge{\@setfontsize\xlarge\@xivpt{16.8}}%!
    \def\ysmall{\@setfontsize\ysmall\@viiipt{9.6}%
     \abovedisplayskip 5\p@ \@plus 1\p@ \@minus 0.5\p@
     \abovedisplayshortskip 1\p@ \@plus 0.2\p@ minus 0.2pt
     \belowdisplayshortskip 1\p@ \@plus 0.2\p@ minus 0.2pt
     \belowdisplayskip \abovedisplayskip
    }%!
    \def\esmall{\@setfontsize\small\@ixpt{12}%
     \abovedisplayskip 5\p@ \@plus 1\p@ \@minus 0.5\p@
     \abovedisplayshortskip 1\p@ \@plus 0.2\p@ minus 0.2pt
     \belowdisplayshortskip 1\p@ \@plus 0.2\p@ minus 0.2pt
     \belowdisplayskip \abovedisplayskip
    }%!
    \def\small{\@setfontsize\small\@ixpt{10.8}%
     \abovedisplayskip 5\p@ \@plus 1\p@ \@minus 0.5\p@
     \abovedisplayshortskip 1\p@ \@plus 0.2\p@ minus 0.2pt
     \belowdisplayshortskip 1\p@ \@plus 0.2\p@ minus 0.2pt
     \belowdisplayskip \abovedisplayskip
    }%!
    \def\normalsize{%
       \@setfontsize\normalsize\@xpt{12.0}%
       \abovedisplayskip 5\p@ \@plus 1\p@ \@minus 0.5\p@
       \abovedisplayshortskip 1\p@ \@plus 0.2\p@ minus 0.2pt
       \belowdisplayshortskip 1\p@ \@plus 0.2\p@ minus 0.2pt
       \belowdisplayskip \abovedisplayskip
       }

    \def\@listi{\leftmargin\leftmargini
		\parsep 0\p@ \@plus 0.1\p@ \@minus 0.1\p@
		\topsep 0\p@ \@plus 0.1\p@ \@minus  0.1\p@
		\itemsep0\p@ \@plus 0.1\p@ \@minus 0.1\p@}
    \let\@listI\@listi
    \@listi
    \def\@listii {\leftmargin\leftmarginii
		  \labelwidth\leftmarginii
		  \advance\labelwidth-\labelsep
		  \topsep    0\p@ \@plus 0.1\p@ \@minus 0.1\p@
		  \parsep    0\p@ \@plus 0.1\p@  \@minus 0.1\p@
		  \itemsep   0pt}
\fi
\def\tiny{\@setfontsize\tiny\@vpt{6}}%
\normalsize

\setlength\footskip{30\p@}
\advance\footskip 2mm

\if@debug
    \textwidth=190mm
    \headsep=20pt
    \advance\headsep 1mm
    \headheight        12pt
    \hoffset=-1in
    \voffset=-1in
    \advance\hoffset -0.5cm
    \advance\voffset -1cm
    \advance\voffset 2mm
    \oddsidemargin=1.5cm
    \evensidemargin=1.5cm
    \textheight=263mm
\else
    \textwidth=175mm
    \headsep=20pt
    \advance\headsep 1mm
    \headheight        12pt
    \hoffset=-1in
    \voffset=-1in
    \advance\voffset 2mm
    \oddsidemargin=1.5cm
    \evensidemargin=1.5cm
    \textheight=243mm
\fi
\setlength\lineskip{1\p@}
\setlength\normallineskip{1\p@}
\renewcommand\baselinestretch{}
\setlength\parskip{2\p@ \@plus 0.5\p@ minus 0.5pt}

\@lowpenalty   51
\@medpenalty  151
\@highpenalty 301

\setcounter{topnumber}{9}
\renewcommand\topfraction{.99}
\setcounter{bottomnumber}{9}
\setcounter{totalnumber}{9}
\renewcommand\bottomfraction{.99}

\renewcommand\textfraction{.01}
\renewcommand\floatpagefraction{.99}
\setcounter{dbltopnumber}{9}
\renewcommand\dbltopfraction{.99}
\renewcommand\dblfloatpagefraction{.99}

\setlength\floatsep    {10\p@ \@plus 2\p@ \@minus 2\p@}
\setlength\textfloatsep{8\p@ \@plus 2\p@ \@minus 2\p@}
\setlength\intextsep   {8\p@ \@plus 2\p@ \@minus 2\p@}
\setlength\dblfloatsep {8\p@ \@plus 2\p@ \@minus 2\p@}

\usepackage{multirow, dcolumn}
\newcolumntype{v}{>{\columncolor{lgray}%
[\tabcolsep]}c}
\newcolumntype{V}{>{\columncolor{lgray}%
[\tabcolsep]}c}
\newcolumntype{P}[1]{>{\rightskip 0pt plus 1fill\leftskip 0pt}p{#1}}
\newcolumntype{M}[1]{>{\leftskip 0pt \rightskip 0pt plus 1fill}m{#1}}
\newcolumntype{C}[1]{>{\leftskip 0pt plus 1fill\rightskip 0pt plus 1fill}m{#1}}
\newcolumntype{Y}[1]{>{%
\leftskip    = 0pt plus 1fil%
\rightskip   = 0pt plus -1fil%
\parfillskip = 0pt plus 2fil%
\parindent = 0pt}m{#1}}
\newcolumntype{L}[1]{>{%
\leftskip 0pt\rightskip 0pt plus 1fill}m{#1}}
\newcolumntype{x}[1]{>{%
\leftskip 0pt\rightskip 0pt plus 1fill}m{#1}}
\newcolumntype{z}[1]{>{%
\leftskip 0pt plus 1fill\rightskip 0pt plus 1fill}m{#1}}
\newcolumntype{u}[1]{>{\columncolor{lgray}%
[\tabcolsep]\parindent0pt\leftskip 0pt plus 1fill\rightskip 0pt plus 1fill}m{#1}}
\newcolumntype{s}[1]{>{\columncolor{lgray}%
[\tabcolsep]\leftskip 0pt \rightskip 0pt plus 1fill}m{#1}}
\newcolumntype{q}[1]{>{\columncolor{lgray}%
[\tabcolsep]\leftskip 0pt plus 1fill\rightskip 0pt plus 1fill}m{#1}}
\newcolumntype{d}[1]{D{,}{{,}}{#1}}
\newcolumntype{.}[1]{D{.}{{,}}{#1}}
\newcolumntype{;}[1]{D{,}{{\mathbf{,}}}{#1}}
\usepackage{amsmath,multirow, array}
\usepackage{color, graphicx, url}
\usepackage[breaklinks=true,
            colorlinks=true,
	    linkcolor=navy,
	    anchorcolor=navy,
	    citecolor=navy,
	    filecolor=navy,
	    urlcolor=navy]
            {hyperref}
\def\UrlBreaks{\do\.\do\@\do\\\do\/\do\!\do\_\do\|\do\;\do\>\do\]%
 \do\)\do\,\do\?\do\'\do+\do\=\do\#\do\-\do\1\do\2\do\3\do\1\do\1\do\6\do\7\do\8\do\9\do\0\do\a\do\b\do\c\do\d\do\e\do\f\do\g\do\i\do\j\do\k\do\n\do\o\do\p\do\q\do\r\do\s\do\u\do\v\do\w\do\x\do\y\do\z\do\%}%
\def\UrlBigBreaks{\do\:\do@url@hyp}%
\def\UrlNoBreaks{\do\(\do\[\do\{\do\<}%
\def\UrlOrds{\do\*\do\-\do\~\do\'\do\"\do\-}%
\def\UrlSpecials{\do\&{\Url@ampersand}\do\ {\Url@space}\do\%{\Url@percent}\do\^^M{\Url@space}%
   \Url@force@Tilde}% package option may force faked text-ascii-tilde

\definecolor{navy}{cmyk}{0.98, 0.84, 0, 0.1}
\definecolor{figcolor}{gray}{0.5}

\usepackage{ifthen}

\usepackage[shrink,spread,checkfootnote,checkfloat]{flushend}
\flushend
\def\licence{%
This work is licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) License.
For~more~information, see \url{https://creativecommons.org/licenses/by/4.0/}}
\def\ps@opening{%
      \def\@oddhead{}
      \def\@evenhead{}
      \def\@oddfoot{\leavevmode{%
	  \raise 3mm\vtop to 0pt{\hsize 4.6cm\switz\baselineskip 9pt\parskip0pt\parindent 0pt\parfillskip 0pt\MakeUppercase{\nameofgame}\vss}~~~~~%
	  \scalebox{1.7}[2.8]{\switzy\@numnum/\@Year}\hfill
	  \raise 3mm\vtop to 0pt{\leftskip 0pt plus 1fill\rightskip 0pt plus 1fill\hsize 8cm\tiny\parskip0pt\parindent 0pt\parfillskip 0pt{\licence}\vss}~~~~~%
	  \hfill
	  \lower 0.3mm\hbox{\normalsize\thepage}}}%
      \def\@evenfoot{\leavevmode\lower 0mm\hbox{\normalsize\thepage}\hfill 
	  \raise 3mm\vtop to 0pt{\leftskip 0pt plus 1fill\rightskip 0pt plus 1fill\hsize 8cm\parskip0pt\parindent 0pt\parfillskip 0pt\tiny{\licence}\vss}\hfill
	  \raise 3mm\vtop to 0pt{\hsize 4.6cm\switz\baselineskip 9pt\parskip0pt\parindent 0pt\parfillskip 0pt\MakeUppercase{\nameofgame}\vss}~~~~~%
	  \scalebox{1.7}[2.8]{\switzy\@numnum/\@Year}%
          }%
      \let\@mkboth\markboth
    \def\sectionmark##1{%
      \markboth {\MakeUppercase{%
        \ifnum \c@secnumdepth >\z@
          \thesection\quad
        \fi
        ##1}}{}}%
    \def\subsectionmark##1{%
      \markright {%
        \ifnum \c@secnumdepth >\@ne
          \thesubsection\quad
        \fi
        ##1}}}
\def\ps@closing{%
      \def\@oddhead{\hfill{\ysmall \@title}}%
      \def\@evenhead{{\ysmall \@authors\hfill}}%
      \def\@oddfoot{}%
      \def\@evenfoot{}%
      \let\@mkboth\markboth
    \def\sectionmark##1{%
      \markboth {\MakeUppercase{%
        \ifnum \c@secnumdepth >\z@
          \thesection\quad
        \fi
        ##1}}{}}%
    \def\subsectionmark##1{%
      \markright {%
        \ifnum \c@secnumdepth >\@ne
          \thesubsection\quad
        \fi
        ##1}}}
\def\ps@headings{%
      \def\@oddhead{\hfill{\ysmall \@title}}%
      \def\@evenhead{{\ysmall \@authors\hfill}}%
      \def\@oddfoot{\leavevmode{%
	  \raise 3mm\vtop to 0pt{\hsize 4.6cm\switz\baselineskip 9pt\parskip0pt\parindent 0pt\parfillskip 0pt\MakeUppercase{\nameofgame}\vss}~~~~~%
	  \scalebox{1.7}[2.8]{\switzy\@numnum/\@Year}\hfill
	  \lower 0.3mm\hbox{\normalsize\thepage}}}%
      \def\@evenfoot{\leavevmode\lower 0mm\hbox{\normalsize\thepage}\hfill 
	  \raise 3mm\vtop to 0pt{\hsize 4.6cm\switz\baselineskip 9pt\parskip0pt\parindent 0pt\parfillskip 0pt\MakeUppercase{\nameofgame}\vss}~~~~~%
	  \scalebox{1.7}[2.8]{\switzy\@numnum/\@Year}}%
      \let\@mkboth\markboth
    \def\sectionmark##1{%
      \markboth {\MakeUppercase{%
        \ifnum \c@secnumdepth >\z@
          \thesection\quad
        \fi
        ##1}}{}}%
    \def\subsectionmark##1{%
      \markright {%
        \ifnum \c@secnumdepth >\@ne
          \thesubsection\quad
        \fi
        ##1}}}
\let\ps@plain=\ps@headings
\def\maketitle{\par
  \begingroup
    \renewcommand\thefootnote{\@fnsymbol\c@footnote}%
    \def\@makefnmark{\rlap{\@textsuperscript{\normalfont\@thefnmark}}}%
    \long\def\@makefntext##1{\parindent 1em\noindent
            \hb@xt@1.8em{%
                \hss\@textsuperscript{\normalfont\@thefnmark}}##1}%
    \if@twocolumn
      \ifnum \col@number=\@ne
        \@maketitle
      \else
        \twocolumn[\@maketitle]%
      \fi
    \else
      \newpage
      \global\@topnum\z@   % Prevents figures from going at top of page.
      \@maketitle
    \fi
    \thispagestyle{opening}\@thanks
  \endgroup
  \setcounter{footnote}{0}%
  \global\let\thanks\relax
  \global\let\maketitle\relax
  \global\let\@maketitle\relax
  \global\let\@thanks\@empty
  \global\let\@date\@empty
  \global\let\title\relax
  \global\let\date\relax
  \global\let\and\relax
}
\newcounter{tmpacount}
\newcounter{tmpbcount}
\newcounter{numofinst}
\newcounter{tmpnumofinst}
\newcounter{numofauthors}
\newcounter{tmpnumofauthors}
\setcounter{numofauthors}{0}
\setcounter{numofinst}{0}

\def\Instytucja#1#2#3{%
    \advance\c@numofinst 1
    \expandafter\xdef\csname i:e:\the\c@numofinst\endcsname{#1}%
    \expandafter\xdef\csname i:n:\the\c@numofinst\endcsname{#2}%
    \expandafter\xdef\csname i:m:\the\c@numofinst\endcsname{#3}%
}
\def\Author#1#2#3#4#5{%
    \advance\c@numofauthors 1
    \expandafter\xdef\csname x:\the\c@numofauthors\endcsname{#1}% tytul
    \expandafter\xdef\csname n:\the\c@numofauthors\endcsname{#2}% imie i nazwisko
    \expandafter\xdef\csname e:\the\c@numofauthors\endcsname{#3}% e-mail
    \expandafter\xdef\csname w:\the\c@numofauthors\endcsname{#4}% adres strony www
    \expandafter\xdef\csname i:\the\c@numofauthors\endcsname{#5}% oznaczenie afiliacji
    \@ifnextchar[%
    {\@Author}%
    {\@Author[]}%
}

\edef\@star{*}
\def\@Author[#1]#2#3#4#5#6{%
    \expandafter\xdef\csname ix:\the\c@numofauthors\endcsname{#1}% oznaczenie dodatkowej afiliacji
    \expandafter\xdef\csname t:\the\c@numofauthors\endcsname{#2}% telefon
    \expandafter\xdef\csname a:\the\c@numofauthors\endcsname{#3}% adres sluzbowy
    % #4 (zdjęcie) nieużywane w jot3 - pole zachowane wyłącznie dla zgodności
    % kolejności argumentów \Author z klasą jot.cls
    \expandafter\xdef\csname na:\the\c@numofauthors\endcsname{#5}% notka biograficzna
    \edef\@tmppos{#6}%
    \ifx\@tmppos\@empty
	\expandafter\xdef\csname in:\the\c@numofauthors\endcsname{*}% kolejność na liście notek
     \else
	\ifx\@tmppos\@star
	    \expandafter\xdef\csname in:\the\c@numofauthors\endcsname{}% wyłączenie
	\else
	    \expandafter\xdef\csname in:\the\c@numofauthors\endcsname{#6}% kolejność na liście notek
	\fi
    \fi
}

\def\@authors{%
	       \setcounter{tmpnumofauthors}{0}%
	       \whiledo{\value{numofauthors} > \value{tmpnumofauthors}}{%
		   \stepcounter{tmpnumofauthors}%
		   \ifnum\c@tmpnumofauthors > 1
		       \ifnum\c@tmpnumofauthors = \c@numofauthors
			   \ifnum\c@numofauthors > 2
			       \def\jot@authsep{,\ and~}%
			   \else
			       \def\jot@authsep{\ and~}%
			   \fi
		       \else
			   \def\jot@authsep{,\ }%
		       \fi
		   \jot@authsep
		   \fi
		   \csname n:\the\c@tmpnumofauthors\endcsname%
	       }%
}
\newbox\fotobox
\newdimen\fotoheight
\def\EndNotes{%
      \penalty 0\relax
      \vskip 0pt\relax
      \parskip =0pt\relax
      \ifnum\value{numofauthors} < 1\relax
        \else
	   \setcounter{tmpbcount}{0}%
	   \whiledo{\value{numofauthors} > \value{tmpbcount}}{%
	       \stepcounter{tmpbcount}%
	       \setcounter{tmpnumofauthors}{0}%
	       \whiledo{\value{numofauthors} > \value{tmpnumofauthors}}{%
		   \stepcounter{tmpnumofauthors}%
		   \expandafter\ifx\csname in:\the\c@tmpnumofauthors\endcsname\@star%
		    \else
		       \expandafter\ifx\csname in:\the\c@tmpnumofauthors\endcsname\@empty%
		        \else
			   \edef\c@currnum{\csname in:\the\c@tmpnumofauthors\endcsname}%
			   \ifnum\c@currnum=\c@tmpbcount
			       \expandafter\xdef\csname in:\the\c@tmpnumofauthors\endcsname{}%
			       \wyswietlnotke{\the\c@tmpnumofauthors}%
			   \fi
		       \fi
	           \fi
	       }%
	   }%
	   \setcounter{tmpnumofauthors}{0}%
	   \whiledo{\value{numofauthors} > \value{tmpnumofauthors}}{%
	       \stepcounter{tmpnumofauthors}%
	       \expandafter\ifx\csname in:\the\c@tmpnumofauthors\endcsname\@empty%
		\else
		   \expandafter\xdef\csname in:\the\c@tmpnumofauthors\endcsname{}%
		   \wyswietlnotke{\the\c@tmpnumofauthors}%
	       \fi
	   }%
      \fi
}

\newbox\@tempboxb
\newdimen\@tempdimb
\def\wyswietlnotke#1{%
   \penalty 0\relax
  \parskip =0pt\relax
   \vskip 5pt plus 1pt minus 1pt\relax
	\noindent{\bfseries
	\csname n:#1\endcsname%
	\expandafter\ifx\csname x:#1\endcsname\@empty
	\else
	    ,\ \csname x:#1\endcsname%
	\fi
	}%
	\expandafter\ifx\csname a:#1\endcsname\@empty
	\else
	    \vglue 0pt
	    {\noindent \csname a:#1\endcsname}\par%
	\fi
	\vglue 0pt
       \noindent\csname na:#1\endcsname%
   \vglue 0pt\relax
    \expandafter\ifx\csname w:#1\endcsname\@empty
    \else
	{\noindent \zielonekolko\ \url{\csname w:#1\endcsname}}\par%
    \fi
    \expandafter\ifx\csname e:#1\endcsname\@empty
    \else
	{\noindent E-mail: \csname e:#1\endcsname}\par%
    \fi
    \noindent \advance\c@numofinst 1\relax
    \edef\@lab{\csname i:#1\endcsname}%
    \ifx\@lab\@empty
    \else
       \setcounter{tmpnumofinst}{0}%
       \whiledo{\value{numofinst} > \value{tmpnumofinst}}{%
	    \expandafter\ifx\csname i:e:\the\c@tmpnumofinst\endcsname\@lab
		\csname i:n:\the\c@tmpnumofinst\endcsname
		\expandafter\ifx\csname i:m:\the\c@tmpnumofinst\endcsname\@empty
		\else
		    \vskip 0pt\url{\csname i:m:\the\c@tmpnumofinst\endcsname}%
		\fi
	    \fi
	    \stepcounter{tmpnumofinst}%
	}%
	\expandafter\ifx\csname ix:#1\endcsname\@empty
	\else
	    \edef\@lab{\csname ix:#1\endcsname}%
	       \setcounter{tmpnumofinst}{0}%
	       \whiledo{\value{numofinst} > \value{tmpnumofinst}}{%
		    \expandafter\ifx\csname i:e:\the\c@tmpnumofinst\endcsname\@lab
			\par\csname i:n:\the\c@tmpnumofinst\endcsname
			\expandafter\ifx\csname i:m:\the\c@tmpnumofinst\endcsname\@empty
			\else
			    \vskip 0pt\url{\csname i:m:\the\c@tmpnumofinst\endcsname}%
			\fi
		    \fi
		    \stepcounter{tmpnumofinst}%
		}%
	\fi
    \fi
}

\def\zielonekolko{\includegraphics[scale=0.6]{figures/zielonekolko.jpg}}
\newbox\@tmpabox
\newdimen\@tmpxdim
\newdimen\@tmpydim

\def\@maketitle{%
  \newpage
  \null
  \vskip -5mm
  \vbox to 0pt{\hbox to 0pt{\vspace{5mm}\hss}\vss}\relax
  \vskip -8mm
  \null
  \hsize=\textwidth
  \leftskip=25pt plus 1fill\rightskip=25pt plus 1fill
  \xLarge{\bfseries\@title}
  \vfill
  \footnotesize
    \vskip 2em%
      \lineskip .5em%
      \Large
      \ifnum\value{numofauthors} < 1
	   \errmessage{Author of this article not defined!}%
        \else
	   \setcounter{tmpnumofauthors}{0}%
	   \whiledo{\value{numofauthors} > \value{tmpnumofauthors}}{%
	       \stepcounter{tmpnumofauthors}%
	       \ifnum\c@tmpnumofauthors > 1
		       \ifnum\c@tmpnumofauthors = \c@numofauthors
			   \ifnum\c@numofauthors > 2
			       \def\jot@authsep{,\ and~}%
			   \else
			       \def\jot@authsep{\ and~}%
			   \fi
		       \else
			   \def\jot@authsep{,\ }%
		       \fi
	       \jot@authsep
	       \fi
	       \csname n:\the\c@tmpnumofauthors\endcsname%
	       \ifnum\c@numofinst > 1
		   \edef\etyk{\csname i:\the\c@tmpnumofauthors\endcsname}%
		   \setcounter{tmpnumofinst}{0}%
		   \ifx\etyk\@empty
		   \else
		       \global\c@tmpacount=0%
		       \whiledo{\value{numofinst} > \value{tmpnumofinst}}{%
			   \stepcounter{tmpnumofinst}%
			   \edef\etyk@{\csname i:e:\the\c@tmpnumofinst\endcsname}%
			   \ifx\etyk@\etyk
			       \global\c@tmpacount=\c@tmpnumofinst
			   \fi
		       }%
		       \ifnum\c@tmpacount=0
			   \errmessage{Error in affiliation}%
		       \else
			  $^{\@arabic\c@tmpacount}$%
		       \fi
		   \fi
		    \expandafter\ifx\csname ix:\the\c@tmpnumofauthors\endcsname\@empty
		    \else
		       \edef\etyk{\csname ix:\the\c@tmpnumofauthors\endcsname}%
		       \setcounter{tmpnumofinst}{0}%
		       \global\c@tmpacount=0%
		       \whiledo{\value{numofinst} > \value{tmpnumofinst}}{%
			   \stepcounter{tmpnumofinst}%
			   \edef\etyk@{\csname i:e:\the\c@tmpnumofinst\endcsname}%
			   \ifx\etyk@\etyk
			       \global\c@tmpacount=\c@tmpnumofinst
			   \fi
		       }%
		       \ifnum\c@tmpacount=0
		           \ifx\etyk\@empty
			   \else
			       \errmessage{Error in affiliation}%
			   \fi
		       \else
			  $^{,\@arabic\c@tmpacount}$%
		       \fi
		   \fi
	       \fi
	   }%
	  \ifnum\value{numofinst} < 1
	       \errmessage{Afiliation not defined!}%
	    \else
	       \vskip 4mm
	       \mdseries\small\itshape
	       \setcounter{tmpnumofinst}{0}%
	       \whiledo{\value{numofinst} > \value{tmpnumofinst}}{%
		   \stepcounter{tmpnumofinst}%
		   \edef\etyk{\csname i:e:\the\c@tmpnumofinst\endcsname}%
		   \ifx\etyk\@empty
		   \else
		       \ifnum\c@tmpnumofinst > 1
			, %
		       \fi
		       \ifnum\value{tmpnumofinst} > 1
			    \par
			\fi
		      \ifnum\c@numofinst > 1
			  $^{\@arabic\c@tmpnumofinst}$%
		      \fi
		       \csname i:n:\the\c@tmpnumofinst\endcsname%
		   \fi
	       }%
	  \fi
      \fi
    \par\rm
    \leftskip=0pt
    \ifx\@doi\@empty
    \else
	\vskip 7mm
	\noindent{\ysmall \@doi}
    \fi
  \vskip 1em}
\def\@hangfrom#1{%
    \setbox\@tempboxa\hbox{{#1}}%
    \noindent\box\@tempboxa}

\setcounter{secnumdepth}{3}
\newcounter {section}
\newcounter {subsection}[section]
\newcounter {subsubsection}[subsection]
\newcounter {paragraph}[subsubsection]
\renewcommand \thesection {\@arabic\c@section}
\renewcommand\thesubsection   {\thesection.\@arabic\c@subsection}
\renewcommand\thesubsubsection   {\thesubsection.\@arabic\c@subsubsection}
\renewcommand\theparagraph    {\thesubsubsection.\@arabic\c@paragraph}
\newcommand\section{\@startsection {section}{1}{\z@}%
                                   {-3ex \@plus -0.3ex \@minus -.2ex}%
                                   {2ex \@plus.1ex}%
                                   {\centering\xlarge}}
\newcommand\subsection{\@startsection{subsection}{2}{\z@}%
                                     {-2ex\@plus -0.2ex \@minus -.1ex}%
                                     {1ex \@plus .2ex}%
				     {\normalfont\itshape\bfseries\raggedright}}
\newcommand\subsubsection{\@startsection{subsubsection}{2}{\z@}%
                                     {-1.2ex\@plus -0.1ex \@minus -.1ex}%
                                     {0.5ex \@plus .2ex}%
                                     {\raggedright\normalsize}}
\newcommand\paragraph{\@startsection{paragraph}{5}{\parindent}%
                                       {3.25ex \@plus1ex \@minus .2ex}%
                                       {-1em}%
                                      {\centering\normalsize}}
\if@twocolumn
  \setlength\leftmargini  {2em}
\else
  \setlength\leftmargini  {2.5em}
\fi
\leftmargin  \leftmargini
\setlength\leftmarginii  {2.2em}
\setlength\leftmarginiii {1.87em}
\setlength\leftmarginiv  {1.7em}
\if@twocolumn
  \setlength\leftmarginv  {.5em}
  \setlength\leftmarginvi {.5em}
\else
  \setlength\leftmarginv  {1em}
  \setlength\leftmarginvi {1em}
\fi
\setlength  \labelsep  {.5em}
\setlength  \labelwidth{\leftmargini}
\addtolength\labelwidth{-\labelsep}
\@beginparpenalty -\@lowpenalty
\@endparpenalty   -\@lowpenalty
\@itempenalty     -\@lowpenalty
\renewcommand\theenumi{\@arabic\c@enumi}
\renewcommand\theenumii{\@alph\c@enumii}
\renewcommand\theenumiii{\@roman\c@enumiii}
\renewcommand\theenumiv{\@Alph\c@enumiv}
\newcommand\labelenumi{\theenumi.}
\newcommand\labelenumii{(\theenumii)}
\newcommand\labelenumiii{\theenumiii.}
\newcommand\labelenumiv{\theenumiv.}
\renewcommand\p@enumii{\theenumi}
\renewcommand\p@enumiii{\theenumi(\theenumii)}
\renewcommand\p@enumiv{\p@enumiii\theenumiii}
\newcommand\labelitemi{\textbullet}
\newcommand\labelitemii{\normalfont\bfseries \textendash}
\newcommand\labelitemiii{\textasteriskcentered}
\newcommand\labelitemiv{\textperiodcentered}
\newenvironment{description}
               {\list{}{\labelwidth\z@ \itemindent-\leftmargin
                        \let\makelabel\descriptionlabel}}
               {\endlist}
\newcommand*\descriptionlabel[1]{\hspace\labelsep
                                \normalfont\bfseries #1}
\newenvironment{quotation}
               {\list{}{\listparindent 1.5em%
                        \itemindent    \listparindent
                        \rightmargin   \leftmargin
                        \parsep        \z@ \@plus\p@}%
                \item\relax}
               {\endlist}
\newenvironment{quote}
               {\list{}{\rightmargin\leftmargin}%
                \item\relax}
               {\endlist}
\newcommand\appendix{\par
  \setcounter{section}{0}%
  \setcounter{subsection}{0}%
  \gdef\thesection{\@Alph\c@section}}
\setlength\arraycolsep{5\p@}
\setlength\tabcolsep{6\p@}
\setlength\arrayrulewidth{.4\p@}
\setlength\doublerulesep{2\p@}
\setlength\tabbingsep{\labelsep}
\skip\@mpfootins = \skip\footins
\setlength\fboxsep{0\p@}
\setlength\fboxrule{.4\p@}
\footskip 28pt
\renewcommand \theequation {\@arabic\c@equation}
\newcounter{figure}
\renewcommand \thefigure {\@arabic\c@figure}
\def\fps@figure{tbp}
\def\ftype@figure{1}
\def\ext@figure{lof}
\def\fnump@figure{Fig.~\thefigure}
\def\fnume@figure{Fig.~\thefigure}
\newenvironment{figure}
               {\@float{figure}}
               {\end@float}
\newenvironment{figure*}
               {\@dblfloat{figure}}
               {\end@dblfloat}
\newcounter{table}
\renewcommand\thetable{\@arabic\c@table}
\def\fps@table{tbp}
\def\ftype@table{2}
\def\ext@table{lot}
\def\fnump@table{Tab.~\thetable}
\def\fnume@table{Tab.~\thetable}
\newenvironment{table}
               {\@float{table}}
               {\end@float}
\newenvironment{table*}
               {\@dblfloat{table}}
               {\end@dblfloat}
\setlength\abovecaptionskip{4\p@}
\setlength\belowcaptionskip{0\p@}
\long\def\@MakeCaption#1#2#3{%
  \bgroup
      \vskip\abovecaptionskip
      \small
\leftskip 0pt\rightskip 0pt\parfillskip =0pt plus 1 fil\relax
     \noindent%\kern-\wd\@tempboxa\hbox to \wd\@tempboxa
     {\bfseries #1.\ }#3%\relax
      \vskip\belowcaptionskip
  \egroup}

\def\Caption{%
   \ifx\@captype\@undefined
     \@latex@error{\noexpand\caption outside float}\@ehd
   \fi
   \@Caption\@captype%
}
\def\@@@@table{table}
\long\def\@Caption#1#2{%
  \refstepcounter\@captype
  \begingroup
      \def\@@@table{#1}%
      \ifnum\strcmp{\@@@@table}{\@@@table}=0%
	    \setlength\abovecaptionskip{0\p@}%
	    \setlength\belowcaptionskip{6\p@}%
	\fi
	\par
	\@MakeCaption{\csname fnump@#1\endcsname}{\csname fnume@#1\endcsname}{\ignorespaces #2}%
  \endgroup}

\DeclareOldFontCommand{\rm}{\normalfont\rmfamily}{\mathrm}
\DeclareOldFontCommand{\sf}{\normalfont}{\mathsf}
\DeclareOldFontCommand{\tt}{\normalfont\ttfamily}{\mathtt}
\DeclareOldFontCommand{\bf}{\normalfont\bfseries}{\mathbf}
\DeclareOldFontCommand{\it}{\normalfont\itshape}{\mathit}
\DeclareOldFontCommand{\sl}{\normalfont\slshape}{\@nomath\sl}
\DeclareOldFontCommand{\sc}{\normalfont\scshape}{\@nomath\sc}
\DeclareRobustCommand*\cal{\@fontswitch\relax\mathcal}
\DeclareRobustCommand*\mit{\@fontswitch\relax\mathnormal}
\newcommand\@pnumwidth{1.55em}
\newcommand\@tocrmarg{2.55em}
\newcommand\@dotsep{4.5}
\setcounter{tocdepth}{3}
\newcommand\tableofcontents{%
    }
\newcommand*\l@section[2]{%
  \ifnum \c@tocdepth >\z@
    \addpenalty\@secpenalty
    \addvspace{1.0em \@plus\p@}%
    \setlength\@tempdima{1.5em}%
    \begingroup
      \parindent \z@ \rightskip \@pnumwidth
      \parfillskip -\@pnumwidth
      \leavevmode \bfseries
      \advance\leftskip\@tempdima
      \hskip -\leftskip
      #1\nobreak\hfil \nobreak\hb@xt@\@pnumwidth{\hss #2}\par
    \endgroup
  \fi}
\newcommand*\l@subsection{\@dottedtocline{2}{1.5em}{2.3em}}
\newcommand*\l@subsubsection{\@dottedtocline{3}{3.8em}{3.2em}}
\newcommand*\l@paragraph{\@dottedtocline{4}{7.0em}{4.1em}}
\newcommand*\l@subparagraph{\@dottedtocline{5}{10em}{5em}}
\newcommand\listoffigures{%
    \section*{\listfigurename}%
      \@mkboth{\MakeUppercase\listfigurename}%
              {\MakeUppercase\listfigurename}%
    \@starttoc{lof}%
    }
\newcommand*\l@figure{\@dottedtocline{1}{1.5em}{2.3em}}
\newcommand\listoftables{%
    \section*{\listtablename}%
      \@mkboth{%
          \MakeUppercase\listtablename}%
         {\MakeUppercase\listtablename}%
    \@starttoc{lot}%
    }
\let\l@table\l@figure
\newdimen\bibindent
\setlength\bibindent{0.0ex}
\newenvironment{thebibliography}[1]
     {\section*{References}%
      \list{\@biblabel{\@arabic\c@enumiv}}%
           {\settowidth\labelwidth{\@biblabel{#1}}%
            \leftmargin\labelwidth
	    \itemsep 0pt\parsep=0pt\relax
	    \parskip 0pt\relax
	    \topsep=0pt\relax
	    \partopsep 0pt\relax
            \advance\leftmargin\labelsep
            \usecounter{enumiv}%
            \let\p@enumiv\@empty
            \renewcommand\theenumiv{\@arabic\c@enumiv}}%
      \sloppy
      \clubpenalty4000
      \@clubpenalty \clubpenalty
      \widowpenalty4000%
      \sfcode`\.\@m
      \ysmall}
     {\nobreak\vskip 5pt\centerline{\hbox to 2cm{\hrulefill}}\par%
     \def\@noitemerr{\@latex@warning{Empty `thebibliography' environment}}%
      \endlist}
\newcommand\newblock{\hskip .11em\@plus.33em\@minus.07em}
\newenvironment{theindex}
               {\if@twocolumn
                  \@restonecolfalse
                \else
                  \@restonecoltrue
                \fi
                \twocolumn[\section*{\indexname}]%
                \@mkboth{\MakeUppercase\indexname}%
                        {\MakeUppercase\indexname}%
                \parindent\z@
                \parskip\z@ \@plus .3\p@\relax
                \columnseprule \z@
                \columnsep 7mm
                \let\item\@idxitem}
               {\if@restonecol\onecolumn\else\clearpage\fi}
\newcommand\@idxitem{\par\hangindent 40\p@}
\newcommand\subitem{\@idxitem \hspace*{20\p@}}
\newcommand\subsubitem{\@idxitem \hspace*{30\p@}}
\newcommand\indexspace{\par \vskip 10\p@ \@plus5\p@ \@minus3\p@\relax}
\renewcommand\footnoterule{%
  \kern-3\p@
  \hrule\@width.4\columnwidth
  \kern2.6\p@}
\newcommand\@makefntext[1]{%
    \parindent 1em%
    \noindent
    \hb@xt@1.8em{\hss\@makefnmark}#1}
\providecommand\contentsname{Contents}
\providecommand\listfigurename{List of Figures}
\providecommand\listtablename{List of Tables}
\providecommand\indexname{Index}
\providecommand\figurename{Fig.}
\providecommand\tablename{Tab.}
\providecommand\appendixname{Appendix}
\def\today{\ifcase\month\or
  January\or February\or March\or April\or May\or June\or
  July\or August\or September\or October\or November\or December\fi
  \space\number\day, \number\year}
\setlength\columnsep{7mm}
\setlength\columnseprule{0\p@}
\pagenumbering{arabic}

\if@twoside
\else
  \raggedbottom
\fi
\if@twocolumn
  \twocolumn
  \sloppy
  \flushbottom
\else
  \onecolumn
\fi
\pagestyle{headings}
\parindent=0em
\renewcommand{\@seccntformat}[1]{\csname the#1\endcsname.~}
\newbox\@@abstract
\newenvironment{xAbstract}
    {\small\noindent\bfseries Abstract --- \setbox\@@abstract=\hbox\bgroup}
    {\egroup%
    \unhcopy\@@abstract
    \@ifundefined{@nkeywords}
                {}%
		{\vskip 0.5ex
		 \noindent
		 {\small\bfseries\itshape Keywords --- }
		 {\small\bfseries\itshape \@nkeywords}}%
		 \vskip 4ex
		 \global\everypar{\hskip-\parindent\everypar{}}}
\usepackage{enumitem}
\setenumerate{parsep=3pt, itemsep=0pt, topsep=-3pt, partopsep=3pt, leftmargin=*}
\setenumerate[1]{label=\arabic*), listparindent=0em}
\setenumerate[2]{label=\alph*)}
\setitemize{parsep=3pt, itemsep=0pt, topsep=-3pt, partopsep=3pt, label={--}, itemindent=0pt, labelwidth=1em, leftmargin=*}

\def\texttilde{\char"8C}

\RequirePackage[QX]{fontenc}
\RequirePackage{fontspec}
\usepackage[plmath]{polski}
\setmainfont{texgyretermes-regular.otf}
           [BoldFont = texgyretermes-bold.otf,
	   ItalicFont = texgyretermes-italic.otf,
	   BoldItalicFont = texgyretermes-bolditalic.otf]
\DeclareSymbolFont{uletters}     {QX}{qtm} {m}{n}
\SetSymbolFont{uletters}  {bold}{QX}{qtm} {b}{n}
\DeclareMathSymbol{\uppi}{\mathord}{uletters}{"4}
\DeclareMathSymbol{\upmi}{\mathord}{uletters}{"7}
\DeclareMathSymbol{\upbeta}{\mathord}{uletters}{"2}
\DeclareMathSymbol{\upalpha}{\mathord}{uletters}{"0}
\DeclareMathSymbol{\updelta}{\mathord}{uletters}{"3}
\DeclareMathSymbol{\cirkledR}{\mathord}{uletters}{"A3}
\DeclareMathSymbol{\cirkledC}{\mathord}{uletters}{"A4}
\DeclareMathSymbol{\bigdot}{\mathord}{uletters}{"B4}

\usepackage[sort]{cite}
\def\citepunct{], [}
\def\citemid{; }
\def\citedash{]\kern 0.4pt--\hskip 0.3pt\penalty\citepunctpenalty[}

\let\bf\bfseries
\frenchspacing
\def\@fnsymbol#1{\ensuremath{\ifcase#1\or *\or **\or *{*}*\or *{*}*{*}\or *{*}*{*}*
  \else\@ctrerr\fi}}
\AtBeginDocument{%
    \setfirstpage
   \language 0
}
%
  \AtEndDocument{%
    \EndNotes
    \vskip 0pt\relax
    \thispagestyle{closing}%
    \writecontents
    \write18{perl bib.pl biblio.tmp}\relax
}
\def\@@authors{%
      \def\tmp{}%
      \def\sep{}%
       \setcounter{tmpnumofauthors}{0}%
       \whiledo{\value{numofauthors} > \value{tmpnumofauthors}}{%
	   \stepcounter{tmpnumofauthors}%
	   \ifnum\c@tmpnumofauthors > 1
	       \ifnum\c@tmpnumofauthors = \c@numofauthors
		   \ifnum\c@numofauthors > 2
			\edef\sep{, and }%
		   \else
			\edef\sep{ and }%
		   \fi
	       \else
		    \edef\sep{, }%
	       \fi
	   \fi
	   \edef\tmp{\tmp\sep \csname n:\the\c@tmpnumofauthors\endcsname}%
	}%
    \protected@write\w@contents{}{\tmp\space	\the\@firstpage-\the\@lastpage}%
}%
\def\writecontents{%
    \openout\w@firstpage=firstpage.aux
    \write\w@firstpage{\string\makeatletter}\relax
    \write\w@firstpage{\string\@firstpage=\the\c@page}\relax
    \closeout\w@firstpage
    \write18{copy firstpage.aux ..}\relax
    \openout\w@contents=contents.txt
    \@lastpage=\c@page
    \def\nobreakspace##1{ }\relax
    %\write\w@contents {==============================================================}%
    \write\w@contents {\@@doi}%
    \write\w@contents {\@title}%
    \@@authors
    \closeout\w@contents
    \write18{type contents.txt >>../contents.txt}\relax
    \write18{type abstract.txt >>../contents.txt}\relax
}
\def\@biblabel#1{[#1]}

\newdimen\@tempDdim
\newcount\@tempDcount
\newbox\@tempDbox
\widowpenalty=10000
\clubpenalty=10000
\def\@paper{{\includegraphics{figures/paper}}}

%(175-7)/2 -2=168/2  - 2=82
\def\ffig{%
      \@ifnextchar[% ]
      {\@@ffig}%
      {\@@ffig[]}%
}
\def\@@ffig[#1]#2{%
      \@ifnextchar[% ]
      {\@@@ffig[#1]#2}%
      {\@@@ffig[#1]#2[0pt]}%
}
\def\@@@ffig[#1]#2[#3]{%
    \textcolor{figcolor}{%
	\x@fboxsep=#3\relax
	\fboxrule=1mm
	\parskip =0pt
	\@tempdima=\linewidth
	\advance\@tempdima -2mm
	\noindent\fbox{\hbox to \@tempdima{\hss\includegraphics[#1]{figures/#2}\hss}}%
    }\ignorespaces
}%

\def\pseudoffig#1{%
    \textcolor{figcolor}{%
	\fboxsep=0mm
	\fboxrule=1mm
	\parskip =0pt
	\fbox{\hbox to 82mm{\hfill\textcolor{black}{#1}\hfill}}%
    }\ignorespaces
}%
\def\elabel#1{\label{e:#1}}
\def\eref#1{(\ref{e:#1})}
\def\flabel#1{\label{f:#1}}
\def\fref#1{\ref{f:#1}}
\def\tlabel#1{\label{t:#1}}
\def\tref#1{\ref{t:#1}}
\def\pagecheck#1{% skip to new page if less than #1 left on this one
   \dimen@=\pagegoal                            % get total page size
   \advance\dimen@ by -\pagetotal               % get page space remaining
   \ifdim\dimen@>0pt\relax                            % is there some left, but
       \ifdim\dimen@< #1\relax                      % not enough to look good?
	  \break\fi\fi                        % then skip to new page
   }
\def\etal{\textit{et al.}}
\let\@eqnarray\eqnarray
\def\eqnarray{\esmall
\@eqnarray}

\let\@equation\equation
\def\equation{\esmall
\@equation}
\def\ppoddzielajaca{\kern 0.6pt--\kern -1.8pt}
\def\arraystretch{1.3}
\arraycolsep=2pt
\newdimen\x@fboxsep
\def\@frameb@x#1{%
  \@tempdima\fboxrule
  \advance\@tempdima\x@fboxsep
  \advance\@tempdima\dp\@tempboxa
  \hbox{%
    \lower\@tempdima\hbox{%
      \vbox{%
        \hrule\@height\fboxrule
        \hbox{%
          \vrule\@width\fboxrule
          #1%
          \vbox{%
            \vskip\x@fboxsep
            \box\@tempboxa
            \vskip\x@fboxsep}%
          #1%
          \vrule\@width\fboxrule}%
          \hrule\@height\fboxrule}%
                          }%
        }%
}
\newread\r@contents
\newwrite\w@contents

\newread\r@firstpage
\newwrite\w@firstpage

\def\setfirstpage{%
    \immediate\openin\r@firstpage=../firstpage.aux
    \ifeof\r@firstpage
       \c@page=\@firstpage
    \else
	\input ../firstpage.aux
	\advance\@firstpage 1\relax
	\ifodd\@firstpage
	\else
	    \advance\@firstpage 1\relax
	\fi
	\c@page=\@firstpage
    \fi
}
\let\oldsum=\sum
\def\sum{\oldsum\limits}

\DeclareRobustCommand\overvector[1]
     {\mathop{\vbox{\m@th\ialign{##\crcr\noalign{\kern3\p@}%
      \rightarrowfill\crcr\noalign{\kern1\p@\nointerlineskip}%
      $\hfil\displaystyle{#1}\hfil$\crcr}}}\limits}
\usepackage{abstract}

\gdef\jot@dblcol{%
  \if@firstcolumn
    \global\@firstcolumnfalse
    \global\setbox\@leftcolumn\copy\@outputbox
  \else
    \global\@firstcolumntrue
    \setbox\@outputbox\vbox{%
      \hb@xt@\textwidth{%
        \hb@xt@\columnwidth{\box\@leftcolumn\hss}%  lewa kolumna
        \hfil{\normalcolor\vrule\@width\columnseprule}\hfil
        \hb@xt@\columnwidth{\box\@outputbox\hss}}}% prawa kolumna
    \ifvoid\hold@viper
    \else
      \setbox\@outputbox\vbox to\textheight{%
        \box\hold@viper
        \box\@outputbox
        \vss}%
    \fi
    \@combinedblfloats
    \@outputpage
    \begingroup
      \@dblfloatplacement\@startdblcolumn
      \loop\if@fcolmade\@outputpage\@startdblcolumn\repeat
    \endgroup
  \fi}
\gdef\jot@opcol{%
  \if@twocolumn
    \@outputdblcol
  \else
    \@outputpage
  \fi}

\gdef\jot@output{%
  \let\par\@@par
  \ifnum\outputpenalty<-\@M
    \@specialoutput
  \else
    \@makecol
    \@outputdblcol
    \global\@mparbottom\z@
    \global\@textfloatsheight\z@
    \@floatplacement
    \@startcolumn
    \loop\if@fcolmade
      \@outputdblcol
      \global\@mparbottom\z@
      \global\@textfloatsheight\z@
      \@floatplacement
      \@startcolumn
    \repeat
  \fi
  \ifnum\outputpenalty>-\@Miv
    \ifdim\@colroom<1.5\baselineskip
      \ifdim\@colroom<\textheight
        \@emptycol
      \else
        \global\vsize\@colroom
      \fi
    \else
      \global\vsize\@colroom
    \fi
  \else
    \global\vsize\maxdimen
  \fi}
\output\expandafter{\jot@output}

\AtBeginDocument{%
  \output\expandafter{\jot@output}%
  \global\let\@opcol\jot@opcol
  \global\let\@outputdblcol\jot@dblcol
  \@ifundefined{saved@orig@@outputdblcol}{}{%
    \global\let\saved@orig@@outputdblcol\jot@dblcol}%
}

\endinput
