/********************************************************************************
** Form generated from reading UI file 'MainWindow.ui'
**
** Created by: Qt User Interface Compiler version 5.15.3
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_MAINWINDOW_H
#define UI_MAINWINDOW_H

#include <QtCore/QVariant>
#include <QtWidgets/QAction>
#include <QtWidgets/QApplication>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QDockWidget>
#include <QtWidgets/QGridLayout>
#include <QtWidgets/QHeaderView>
#include <QtWidgets/QLabel>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QMainWindow>
#include <QtWidgets/QMenu>
#include <QtWidgets/QMenuBar>
#include <QtWidgets/QPlainTextEdit>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QSpinBox>
#include <QtWidgets/QTableView>
#include <QtWidgets/QToolButton>
#include <QtWidgets/QWidget>
#include "Screen.h"

QT_BEGIN_NAMESPACE

class Ui_MainWindow
{
public:
    QAction *actionOpen;
    QAction *actionPause;
    QAction *actionStep;
    QAction *actionLoadState;
    QAction *actionSaveState;
    QAction *actionReset;
    QAction *actionLoadVars;
    QAction *actionSaveVars;
    QAction *actionLoadSearch;
    QAction *actionSaveSearch;
    QAction *actionEditScenario;
    QAction *actionScreenshot;
    QAction *actionAutosaveVariables;
    QAction *actionAutosaveSearches;
    QAction *actionAutosaveScenario;
    QAction *actionIntegrate;
    QAction *actionLoadExisting;
    QAction *actionShowCheats;
    QAction *actionShowVariables;
    QAction *actionShowScenario;
    QAction *actionShowSearch;
    QAction *actionPlayMovie;
    QAction *actionRecordMovie;
    QAction *actionStopMovie;
    QAction *actionEpisodeRecording;
    QAction *actionControls;
    QAction *actionHardReset;
    QAction *actionOpenAny;
    QAction *actionSetDataDirectory;
    QAction *actionLoadScenario;
    QWidget *centralwidget;
    QGridLayout *gridLayout_4;
    Screen *screen;
    QMenuBar *menubar;
    QMenu *menuFile;
    QMenu *menuData;
    QMenu *menuWindow;
    QDockWidget *variableView;
    QWidget *dockWidgetContents;
    QGridLayout *gridLayout_2;
    QSpinBox *variableAddress;
    QToolButton *variableRemove;
    QTableView *variables;
    QToolButton *variableAdd;
    QLineEdit *variableType;
    QLineEdit *variableName;
    QDockWidget *scenarioView;
    QWidget *dockWidgetContents_2;
    QGridLayout *gridLayout_3;
    QLabel *label_2;
    QLabel *label;
    QLabel *cumReward;
    QPushButton *resetScenario;
    QLabel *didEnd;
    QLabel *reward;
    QLabel *label_5;
    QLabel *movie;
    QLabel *label_4;
    QLabel *label_3;
    QLabel *done;
    QLabel *label_6;
    QLabel *label_7;
    QLabel *frame;
    QLabel *ts;
    QDockWidget *searchView;
    QWidget *dockWidgetContents_3;
    QGridLayout *gridLayout;
    QToolButton *searchSubmit;
    QTableView *search;
    QLineEdit *searchName;
    QComboBox *searchType;
    QToolButton *searchRemove;
    QTableView *searchResults;
    QSpinBox *searchValue;
    QToolButton *searchMigrate;
    QDockWidget *cheatView;
    QWidget *dockWidgetContents_4;
    QGridLayout *gridLayout_5;
    QTableView *cheats;
    QLineEdit *cheatName;
    QToolButton *cheatAdd;
    QToolButton *cheatRemove;
    QPlainTextEdit *cheatValue;

    void setupUi(QMainWindow *MainWindow)
    {
        if (MainWindow->objectName().isEmpty())
            MainWindow->setObjectName(QString::fromUtf8("MainWindow"));
        MainWindow->resize(1055, 650);
        MainWindow->setDocumentMode(true);
        MainWindow->setDockNestingEnabled(true);
        actionOpen = new QAction(MainWindow);
        actionOpen->setObjectName(QString::fromUtf8("actionOpen"));
        actionPause = new QAction(MainWindow);
        actionPause->setObjectName(QString::fromUtf8("actionPause"));
        actionPause->setCheckable(true);
        actionPause->setEnabled(false);
        actionStep = new QAction(MainWindow);
        actionStep->setObjectName(QString::fromUtf8("actionStep"));
        actionStep->setEnabled(false);
        actionLoadState = new QAction(MainWindow);
        actionLoadState->setObjectName(QString::fromUtf8("actionLoadState"));
        actionSaveState = new QAction(MainWindow);
        actionSaveState->setObjectName(QString::fromUtf8("actionSaveState"));
        actionReset = new QAction(MainWindow);
        actionReset->setObjectName(QString::fromUtf8("actionReset"));
        actionReset->setEnabled(false);
        actionLoadVars = new QAction(MainWindow);
        actionLoadVars->setObjectName(QString::fromUtf8("actionLoadVars"));
        actionLoadVars->setEnabled(false);
        actionSaveVars = new QAction(MainWindow);
        actionSaveVars->setObjectName(QString::fromUtf8("actionSaveVars"));
        actionSaveVars->setEnabled(false);
        actionLoadSearch = new QAction(MainWindow);
        actionLoadSearch->setObjectName(QString::fromUtf8("actionLoadSearch"));
        actionLoadSearch->setEnabled(false);
        actionSaveSearch = new QAction(MainWindow);
        actionSaveSearch->setObjectName(QString::fromUtf8("actionSaveSearch"));
        actionSaveSearch->setEnabled(false);
        actionEditScenario = new QAction(MainWindow);
        actionEditScenario->setObjectName(QString::fromUtf8("actionEditScenario"));
        actionEditScenario->setEnabled(false);
        actionScreenshot = new QAction(MainWindow);
        actionScreenshot->setObjectName(QString::fromUtf8("actionScreenshot"));
        actionAutosaveVariables = new QAction(MainWindow);
        actionAutosaveVariables->setObjectName(QString::fromUtf8("actionAutosaveVariables"));
        actionAutosaveVariables->setCheckable(true);
        actionAutosaveVariables->setChecked(true);
        actionAutosaveSearches = new QAction(MainWindow);
        actionAutosaveSearches->setObjectName(QString::fromUtf8("actionAutosaveSearches"));
        actionAutosaveSearches->setCheckable(true);
        actionAutosaveScenario = new QAction(MainWindow);
        actionAutosaveScenario->setObjectName(QString::fromUtf8("actionAutosaveScenario"));
        actionAutosaveScenario->setCheckable(true);
        actionAutosaveScenario->setChecked(true);
        actionIntegrate = new QAction(MainWindow);
        actionIntegrate->setObjectName(QString::fromUtf8("actionIntegrate"));
        actionLoadExisting = new QAction(MainWindow);
        actionLoadExisting->setObjectName(QString::fromUtf8("actionLoadExisting"));
        actionShowCheats = new QAction(MainWindow);
        actionShowCheats->setObjectName(QString::fromUtf8("actionShowCheats"));
        actionShowCheats->setCheckable(true);
        actionShowVariables = new QAction(MainWindow);
        actionShowVariables->setObjectName(QString::fromUtf8("actionShowVariables"));
        actionShowVariables->setCheckable(true);
        actionShowVariables->setChecked(true);
        actionShowScenario = new QAction(MainWindow);
        actionShowScenario->setObjectName(QString::fromUtf8("actionShowScenario"));
        actionShowScenario->setCheckable(true);
        actionShowScenario->setChecked(true);
        actionShowSearch = new QAction(MainWindow);
        actionShowSearch->setObjectName(QString::fromUtf8("actionShowSearch"));
        actionShowSearch->setCheckable(true);
        actionShowSearch->setChecked(true);
        actionPlayMovie = new QAction(MainWindow);
        actionPlayMovie->setObjectName(QString::fromUtf8("actionPlayMovie"));
        actionRecordMovie = new QAction(MainWindow);
        actionRecordMovie->setObjectName(QString::fromUtf8("actionRecordMovie"));
        actionStopMovie = new QAction(MainWindow);
        actionStopMovie->setObjectName(QString::fromUtf8("actionStopMovie"));
        actionEpisodeRecording = new QAction(MainWindow);
        actionEpisodeRecording->setObjectName(QString::fromUtf8("actionEpisodeRecording"));
        actionEpisodeRecording->setCheckable(true);
        actionControls = new QAction(MainWindow);
        actionControls->setObjectName(QString::fromUtf8("actionControls"));
        actionControls->setEnabled(false);
        actionHardReset = new QAction(MainWindow);
        actionHardReset->setObjectName(QString::fromUtf8("actionHardReset"));
        actionHardReset->setEnabled(false);
        actionOpenAny = new QAction(MainWindow);
        actionOpenAny->setObjectName(QString::fromUtf8("actionOpenAny"));
        actionSetDataDirectory = new QAction(MainWindow);
        actionSetDataDirectory->setObjectName(QString::fromUtf8("actionSetDataDirectory"));
        actionLoadScenario = new QAction(MainWindow);
        actionLoadScenario->setObjectName(QString::fromUtf8("actionLoadScenario"));
        centralwidget = new QWidget(MainWindow);
        centralwidget->setObjectName(QString::fromUtf8("centralwidget"));
        gridLayout_4 = new QGridLayout(centralwidget);
        gridLayout_4->setObjectName(QString::fromUtf8("gridLayout_4"));
        gridLayout_4->setContentsMargins(0, 0, 0, 0);
        screen = new Screen(centralwidget);
        screen->setObjectName(QString::fromUtf8("screen"));
        QSizePolicy sizePolicy(QSizePolicy::MinimumExpanding, QSizePolicy::MinimumExpanding);
        sizePolicy.setHorizontalStretch(1);
        sizePolicy.setVerticalStretch(0);
        sizePolicy.setHeightForWidth(screen->sizePolicy().hasHeightForWidth());
        screen->setSizePolicy(sizePolicy);

        gridLayout_4->addWidget(screen, 0, 0, 1, 1);

        MainWindow->setCentralWidget(centralwidget);
        menubar = new QMenuBar(MainWindow);
        menubar->setObjectName(QString::fromUtf8("menubar"));
        menubar->setGeometry(QRect(0, 0, 1055, 22));
        menuFile = new QMenu(menubar);
        menuFile->setObjectName(QString::fromUtf8("menuFile"));
        menuData = new QMenu(menubar);
        menuData->setObjectName(QString::fromUtf8("menuData"));
        menuWindow = new QMenu(menubar);
        menuWindow->setObjectName(QString::fromUtf8("menuWindow"));
        MainWindow->setMenuBar(menubar);
        variableView = new QDockWidget(MainWindow);
        variableView->setObjectName(QString::fromUtf8("variableView"));
        dockWidgetContents = new QWidget();
        dockWidgetContents->setObjectName(QString::fromUtf8("dockWidgetContents"));
        gridLayout_2 = new QGridLayout(dockWidgetContents);
        gridLayout_2->setObjectName(QString::fromUtf8("gridLayout_2"));
        variableAddress = new QSpinBox(dockWidgetContents);
        variableAddress->setObjectName(QString::fromUtf8("variableAddress"));
        variableAddress->setAccelerated(true);
        variableAddress->setMinimum(0);
        variableAddress->setMaximum(2147483647);
        variableAddress->setDisplayIntegerBase(16);

        gridLayout_2->addWidget(variableAddress, 2, 0, 1, 1);

        variableRemove = new QToolButton(dockWidgetContents);
        variableRemove->setObjectName(QString::fromUtf8("variableRemove"));

        gridLayout_2->addWidget(variableRemove, 1, 3, 1, 1);

        variables = new QTableView(dockWidgetContents);
        variables->setObjectName(QString::fromUtf8("variables"));
        variables->setAlternatingRowColors(true);
        variables->setSelectionBehavior(QAbstractItemView::SelectRows);
        variables->setShowGrid(false);
        variables->horizontalHeader()->setDefaultSectionSize(60);
        variables->horizontalHeader()->setHighlightSections(false);
        variables->horizontalHeader()->setStretchLastSection(true);
        variables->verticalHeader()->setVisible(false);

        gridLayout_2->addWidget(variables, 0, 0, 1, 4);

        variableAdd = new QToolButton(dockWidgetContents);
        variableAdd->setObjectName(QString::fromUtf8("variableAdd"));

        gridLayout_2->addWidget(variableAdd, 1, 2, 1, 1);

        variableType = new QLineEdit(dockWidgetContents);
        variableType->setObjectName(QString::fromUtf8("variableType"));
        variableType->setMaxLength(4);

        gridLayout_2->addWidget(variableType, 2, 1, 1, 3);

        variableName = new QLineEdit(dockWidgetContents);
        variableName->setObjectName(QString::fromUtf8("variableName"));

        gridLayout_2->addWidget(variableName, 1, 0, 1, 2);

        variableView->setWidget(dockWidgetContents);
        MainWindow->addDockWidget(Qt::RightDockWidgetArea, variableView);
        scenarioView = new QDockWidget(MainWindow);
        scenarioView->setObjectName(QString::fromUtf8("scenarioView"));
        QSizePolicy sizePolicy1(QSizePolicy::Preferred, QSizePolicy::Maximum);
        sizePolicy1.setHorizontalStretch(0);
        sizePolicy1.setVerticalStretch(0);
        sizePolicy1.setHeightForWidth(scenarioView->sizePolicy().hasHeightForWidth());
        scenarioView->setSizePolicy(sizePolicy1);
        dockWidgetContents_2 = new QWidget();
        dockWidgetContents_2->setObjectName(QString::fromUtf8("dockWidgetContents_2"));
        gridLayout_3 = new QGridLayout(dockWidgetContents_2);
        gridLayout_3->setObjectName(QString::fromUtf8("gridLayout_3"));
        label_2 = new QLabel(dockWidgetContents_2);
        label_2->setObjectName(QString::fromUtf8("label_2"));

        gridLayout_3->addWidget(label_2, 0, 2, 1, 1);

        label = new QLabel(dockWidgetContents_2);
        label->setObjectName(QString::fromUtf8("label"));

        gridLayout_3->addWidget(label, 0, 0, 1, 1);

        cumReward = new QLabel(dockWidgetContents_2);
        cumReward->setObjectName(QString::fromUtf8("cumReward"));

        gridLayout_3->addWidget(cumReward, 0, 3, 1, 1);

        resetScenario = new QPushButton(dockWidgetContents_2);
        resetScenario->setObjectName(QString::fromUtf8("resetScenario"));
        QSizePolicy sizePolicy2(QSizePolicy::Fixed, QSizePolicy::Fixed);
        sizePolicy2.setHorizontalStretch(0);
        sizePolicy2.setVerticalStretch(0);
        sizePolicy2.setHeightForWidth(resetScenario->sizePolicy().hasHeightForWidth());
        resetScenario->setSizePolicy(sizePolicy2);

        gridLayout_3->addWidget(resetScenario, 4, 2, 1, 2);

        didEnd = new QLabel(dockWidgetContents_2);
        didEnd->setObjectName(QString::fromUtf8("didEnd"));

        gridLayout_3->addWidget(didEnd, 2, 3, 1, 1);

        reward = new QLabel(dockWidgetContents_2);
        reward->setObjectName(QString::fromUtf8("reward"));

        gridLayout_3->addWidget(reward, 0, 1, 1, 1);

        label_5 = new QLabel(dockWidgetContents_2);
        label_5->setObjectName(QString::fromUtf8("label_5"));

        gridLayout_3->addWidget(label_5, 4, 0, 1, 1);

        movie = new QLabel(dockWidgetContents_2);
        movie->setObjectName(QString::fromUtf8("movie"));

        gridLayout_3->addWidget(movie, 4, 1, 1, 1);

        label_4 = new QLabel(dockWidgetContents_2);
        label_4->setObjectName(QString::fromUtf8("label_4"));

        gridLayout_3->addWidget(label_4, 2, 2, 1, 1);

        label_3 = new QLabel(dockWidgetContents_2);
        label_3->setObjectName(QString::fromUtf8("label_3"));

        gridLayout_3->addWidget(label_3, 2, 0, 1, 1);

        done = new QLabel(dockWidgetContents_2);
        done->setObjectName(QString::fromUtf8("done"));

        gridLayout_3->addWidget(done, 2, 1, 1, 1);

        label_6 = new QLabel(dockWidgetContents_2);
        label_6->setObjectName(QString::fromUtf8("label_6"));

        gridLayout_3->addWidget(label_6, 3, 0, 1, 1);

        label_7 = new QLabel(dockWidgetContents_2);
        label_7->setObjectName(QString::fromUtf8("label_7"));

        gridLayout_3->addWidget(label_7, 3, 2, 1, 1);

        frame = new QLabel(dockWidgetContents_2);
        frame->setObjectName(QString::fromUtf8("frame"));

        gridLayout_3->addWidget(frame, 3, 1, 1, 1);

        ts = new QLabel(dockWidgetContents_2);
        ts->setObjectName(QString::fromUtf8("ts"));

        gridLayout_3->addWidget(ts, 3, 3, 1, 1);

        scenarioView->setWidget(dockWidgetContents_2);
        MainWindow->addDockWidget(Qt::RightDockWidgetArea, scenarioView);
        searchView = new QDockWidget(MainWindow);
        searchView->setObjectName(QString::fromUtf8("searchView"));
        dockWidgetContents_3 = new QWidget();
        dockWidgetContents_3->setObjectName(QString::fromUtf8("dockWidgetContents_3"));
        gridLayout = new QGridLayout(dockWidgetContents_3);
        gridLayout->setObjectName(QString::fromUtf8("gridLayout"));
        searchSubmit = new QToolButton(dockWidgetContents_3);
        searchSubmit->setObjectName(QString::fromUtf8("searchSubmit"));

        gridLayout->addWidget(searchSubmit, 2, 2, 1, 1);

        search = new QTableView(dockWidgetContents_3);
        search->setObjectName(QString::fromUtf8("search"));
        search->setAlternatingRowColors(true);
        search->setSelectionBehavior(QAbstractItemView::SelectRows);
        search->setShowGrid(false);
        search->horizontalHeader()->setDefaultSectionSize(60);
        search->horizontalHeader()->setHighlightSections(false);
        search->horizontalHeader()->setStretchLastSection(true);
        search->verticalHeader()->setVisible(false);

        gridLayout->addWidget(search, 0, 0, 1, 4);

        searchName = new QLineEdit(dockWidgetContents_3);
        searchName->setObjectName(QString::fromUtf8("searchName"));

        gridLayout->addWidget(searchName, 2, 0, 1, 2);

        searchType = new QComboBox(dockWidgetContents_3);
        searchType->addItem(QString());
        searchType->addItem(QString());
        searchType->addItem(QString());
        searchType->addItem(QString());
        searchType->addItem(QString());
        searchType->addItem(QString());
        searchType->addItem(QString());
        searchType->setObjectName(QString::fromUtf8("searchType"));

        gridLayout->addWidget(searchType, 3, 0, 1, 1);

        searchRemove = new QToolButton(dockWidgetContents_3);
        searchRemove->setObjectName(QString::fromUtf8("searchRemove"));

        gridLayout->addWidget(searchRemove, 2, 3, 1, 1);

        searchResults = new QTableView(dockWidgetContents_3);
        searchResults->setObjectName(QString::fromUtf8("searchResults"));
        searchResults->setAlternatingRowColors(true);
        searchResults->setSelectionBehavior(QAbstractItemView::SelectRows);
        searchResults->setShowGrid(false);
        searchResults->horizontalHeader()->setDefaultSectionSize(60);
        searchResults->horizontalHeader()->setHighlightSections(false);
        searchResults->horizontalHeader()->setStretchLastSection(true);
        searchResults->verticalHeader()->setVisible(false);

        gridLayout->addWidget(searchResults, 1, 0, 1, 4);

        searchValue = new QSpinBox(dockWidgetContents_3);
        searchValue->setObjectName(QString::fromUtf8("searchValue"));
        QSizePolicy sizePolicy3(QSizePolicy::Preferred, QSizePolicy::Fixed);
        sizePolicy3.setHorizontalStretch(0);
        sizePolicy3.setVerticalStretch(0);
        sizePolicy3.setHeightForWidth(searchValue->sizePolicy().hasHeightForWidth());
        searchValue->setSizePolicy(sizePolicy3);
        searchValue->setAccelerated(true);
        searchValue->setMinimum(-2147483647);
        searchValue->setMaximum(2147483647);

        gridLayout->addWidget(searchValue, 3, 1, 1, 1);

        searchMigrate = new QToolButton(dockWidgetContents_3);
        searchMigrate->setObjectName(QString::fromUtf8("searchMigrate"));

        gridLayout->addWidget(searchMigrate, 3, 2, 1, 2);

        gridLayout->setRowStretch(0, 2);
        gridLayout->setRowStretch(1, 3);
        searchView->setWidget(dockWidgetContents_3);
        MainWindow->addDockWidget(Qt::RightDockWidgetArea, searchView);
        cheatView = new QDockWidget(MainWindow);
        cheatView->setObjectName(QString::fromUtf8("cheatView"));
        cheatView->setVisible(false);
        cheatView->setFloating(false);
        dockWidgetContents_4 = new QWidget();
        dockWidgetContents_4->setObjectName(QString::fromUtf8("dockWidgetContents_4"));
        gridLayout_5 = new QGridLayout(dockWidgetContents_4);
        gridLayout_5->setObjectName(QString::fromUtf8("gridLayout_5"));
        cheats = new QTableView(dockWidgetContents_4);
        cheats->setObjectName(QString::fromUtf8("cheats"));
        cheats->setAlternatingRowColors(true);
        cheats->setSelectionBehavior(QAbstractItemView::SelectRows);
        cheats->setShowGrid(false);
        cheats->horizontalHeader()->setDefaultSectionSize(60);
        cheats->horizontalHeader()->setHighlightSections(false);
        cheats->horizontalHeader()->setStretchLastSection(true);
        cheats->verticalHeader()->setVisible(false);

        gridLayout_5->addWidget(cheats, 0, 0, 1, 3);

        cheatName = new QLineEdit(dockWidgetContents_4);
        cheatName->setObjectName(QString::fromUtf8("cheatName"));

        gridLayout_5->addWidget(cheatName, 1, 0, 1, 1);

        cheatAdd = new QToolButton(dockWidgetContents_4);
        cheatAdd->setObjectName(QString::fromUtf8("cheatAdd"));

        gridLayout_5->addWidget(cheatAdd, 1, 1, 1, 1);

        cheatRemove = new QToolButton(dockWidgetContents_4);
        cheatRemove->setObjectName(QString::fromUtf8("cheatRemove"));

        gridLayout_5->addWidget(cheatRemove, 1, 2, 1, 1);

        cheatValue = new QPlainTextEdit(dockWidgetContents_4);
        cheatValue->setObjectName(QString::fromUtf8("cheatValue"));

        gridLayout_5->addWidget(cheatValue, 2, 0, 1, 3);

        gridLayout_5->setRowStretch(0, 2);
        gridLayout_5->setRowStretch(2, 1);
        cheatView->setWidget(dockWidgetContents_4);
        MainWindow->addDockWidget(Qt::RightDockWidgetArea, cheatView);
        QWidget::setTabOrder(variables, variableName);
        QWidget::setTabOrder(variableName, variableAddress);
        QWidget::setTabOrder(variableAddress, variableType);
        QWidget::setTabOrder(variableType, variableAdd);
        QWidget::setTabOrder(variableAdd, variableRemove);
        QWidget::setTabOrder(variableRemove, resetScenario);
        QWidget::setTabOrder(resetScenario, search);
        QWidget::setTabOrder(search, searchResults);
        QWidget::setTabOrder(searchResults, searchName);
        QWidget::setTabOrder(searchName, searchType);
        QWidget::setTabOrder(searchType, searchValue);
        QWidget::setTabOrder(searchValue, searchSubmit);
        QWidget::setTabOrder(searchSubmit, searchRemove);
        QWidget::setTabOrder(searchRemove, searchMigrate);
        QWidget::setTabOrder(searchMigrate, cheats);
        QWidget::setTabOrder(cheats, cheatName);
        QWidget::setTabOrder(cheatName, cheatValue);
        QWidget::setTabOrder(cheatValue, cheatAdd);
        QWidget::setTabOrder(cheatAdd, cheatRemove);

        menubar->addAction(menuFile->menuAction());
        menubar->addAction(menuData->menuAction());
        menubar->addAction(menuWindow->menuAction());
        menuFile->addAction(actionOpenAny);
        menuFile->addSeparator();
        menuFile->addAction(actionOpen);
        menuFile->addAction(actionIntegrate);
        menuFile->addAction(actionLoadExisting);
        menuFile->addSeparator();
        menuFile->addAction(actionLoadState);
        menuFile->addAction(actionSaveState);
        menuFile->addAction(actionScreenshot);
        menuFile->addSeparator();
        menuFile->addAction(actionReset);
        menuFile->addAction(actionHardReset);
        menuFile->addAction(actionPause);
        menuFile->addAction(actionStep);
        menuFile->addSeparator();
        menuFile->addAction(actionPlayMovie);
        menuFile->addAction(actionRecordMovie);
        menuFile->addAction(actionStopMovie);
        menuFile->addAction(actionEpisodeRecording);
        menuData->addAction(actionLoadVars);
        menuData->addAction(actionSaveVars);
        menuData->addSeparator();
        menuData->addAction(actionLoadSearch);
        menuData->addAction(actionSaveSearch);
        menuData->addSeparator();
        menuData->addAction(actionLoadScenario);
        menuData->addAction(actionEditScenario);
        menuData->addSeparator();
        menuData->addAction(actionAutosaveVariables);
        menuData->addAction(actionAutosaveScenario);
        menuData->addAction(actionAutosaveSearches);
        menuData->addSeparator();
        menuData->addAction(actionSetDataDirectory);
        menuWindow->addAction(actionShowVariables);
        menuWindow->addAction(actionShowScenario);
        menuWindow->addAction(actionShowSearch);
        menuWindow->addAction(actionShowCheats);
        menuWindow->addSeparator();
        menuWindow->addAction(actionControls);

        retranslateUi(MainWindow);
        QObject::connect(cheats, SIGNAL(doubleClicked(QModelIndex)), screen, SLOT(gamesWereBetter()));
        QObject::connect(actionShowVariables, SIGNAL(toggled(bool)), variableView, SLOT(setVisible(bool)));
        QObject::connect(variableView, SIGNAL(visibilityChanged(bool)), actionShowVariables, SLOT(setChecked(bool)));
        QObject::connect(scenarioView, SIGNAL(visibilityChanged(bool)), actionShowScenario, SLOT(setChecked(bool)));
        QObject::connect(searchView, SIGNAL(visibilityChanged(bool)), actionShowSearch, SLOT(setChecked(bool)));
        QObject::connect(cheatView, SIGNAL(visibilityChanged(bool)), actionShowCheats, SLOT(setChecked(bool)));
        QObject::connect(actionShowScenario, SIGNAL(toggled(bool)), scenarioView, SLOT(setVisible(bool)));
        QObject::connect(actionShowSearch, SIGNAL(toggled(bool)), searchView, SLOT(setVisible(bool)));
        QObject::connect(actionShowCheats, SIGNAL(toggled(bool)), cheatView, SLOT(setVisible(bool)));

        QMetaObject::connectSlotsByName(MainWindow);
    } // setupUi

    void retranslateUi(QMainWindow *MainWindow)
    {
        actionOpen->setText(QCoreApplication::translate("MainWindow", "&Load game...", nullptr));
#if QT_CONFIG(shortcut)
        actionOpen->setShortcut(QCoreApplication::translate("MainWindow", "Meta+Ctrl+O", nullptr));
#endif // QT_CONFIG(shortcut)
        actionPause->setText(QCoreApplication::translate("MainWindow", "&Pause", nullptr));
#if QT_CONFIG(shortcut)
        actionPause->setShortcut(QCoreApplication::translate("MainWindow", "Ctrl+P", nullptr));
#endif // QT_CONFIG(shortcut)
        actionStep->setText(QCoreApplication::translate("MainWindow", "Step", nullptr));
#if QT_CONFIG(shortcut)
        actionStep->setShortcut(QCoreApplication::translate("MainWindow", "Ctrl+N", nullptr));
#endif // QT_CONFIG(shortcut)
        actionLoadState->setText(QCoreApplication::translate("MainWindow", "Load state...", nullptr));
#if QT_CONFIG(shortcut)
        actionLoadState->setShortcut(QCoreApplication::translate("MainWindow", "Ctrl+L", nullptr));
#endif // QT_CONFIG(shortcut)
        actionSaveState->setText(QCoreApplication::translate("MainWindow", "Save state...", nullptr));
#if QT_CONFIG(shortcut)
        actionSaveState->setShortcut(QCoreApplication::translate("MainWindow", "Ctrl+S", nullptr));
#endif // QT_CONFIG(shortcut)
        actionReset->setText(QCoreApplication::translate("MainWindow", "Reset", nullptr));
#if QT_CONFIG(shortcut)
        actionReset->setShortcut(QCoreApplication::translate("MainWindow", "Ctrl+R", nullptr));
#endif // QT_CONFIG(shortcut)
        actionLoadVars->setText(QCoreApplication::translate("MainWindow", "Load variables...", nullptr));
        actionSaveVars->setText(QCoreApplication::translate("MainWindow", "Save variables...", nullptr));
        actionLoadSearch->setText(QCoreApplication::translate("MainWindow", "Load search...", nullptr));
        actionSaveSearch->setText(QCoreApplication::translate("MainWindow", "Save search...", nullptr));
        actionEditScenario->setText(QCoreApplication::translate("MainWindow", "Edit scenario...", nullptr));
        actionScreenshot->setText(QCoreApplication::translate("MainWindow", "Screenshot...", nullptr));
        actionAutosaveVariables->setText(QCoreApplication::translate("MainWindow", "Autosave variables", nullptr));
        actionAutosaveSearches->setText(QCoreApplication::translate("MainWindow", "Autosave searches", nullptr));
        actionAutosaveScenario->setText(QCoreApplication::translate("MainWindow", "Autosave scenario", nullptr));
        actionIntegrate->setText(QCoreApplication::translate("MainWindow", "Integrate...", nullptr));
#if QT_CONFIG(shortcut)
        actionIntegrate->setShortcut(QCoreApplication::translate("MainWindow", "Ctrl+Shift+O", nullptr));
#endif // QT_CONFIG(shortcut)
        actionLoadExisting->setText(QCoreApplication::translate("MainWindow", "Load existing...", nullptr));
#if QT_CONFIG(shortcut)
        actionLoadExisting->setShortcut(QCoreApplication::translate("MainWindow", "Ctrl+Alt+O", nullptr));
#endif // QT_CONFIG(shortcut)
        actionShowCheats->setText(QCoreApplication::translate("MainWindow", "Show cheats...", nullptr));
        actionShowVariables->setText(QCoreApplication::translate("MainWindow", "Show variables...", nullptr));
        actionShowScenario->setText(QCoreApplication::translate("MainWindow", "Show scenario info...", nullptr));
        actionShowSearch->setText(QCoreApplication::translate("MainWindow", "Show search...", nullptr));
        actionPlayMovie->setText(QCoreApplication::translate("MainWindow", "Play movie...", nullptr));
        actionRecordMovie->setText(QCoreApplication::translate("MainWindow", "Record movie...", nullptr));
        actionStopMovie->setText(QCoreApplication::translate("MainWindow", "Stop movie", nullptr));
        actionEpisodeRecording->setText(QCoreApplication::translate("MainWindow", "Episode record mode", nullptr));
        actionControls->setText(QCoreApplication::translate("MainWindow", "Controls...", nullptr));
        actionHardReset->setText(QCoreApplication::translate("MainWindow", "Hard reset", nullptr));
#if QT_CONFIG(shortcut)
        actionHardReset->setShortcut(QCoreApplication::translate("MainWindow", "Ctrl+Shift+R", nullptr));
#endif // QT_CONFIG(shortcut)
        actionOpenAny->setText(QCoreApplication::translate("MainWindow", "Open...", nullptr));
#if QT_CONFIG(shortcut)
        actionOpenAny->setShortcut(QCoreApplication::translate("MainWindow", "Ctrl+O", nullptr));
#endif // QT_CONFIG(shortcut)
        actionSetDataDirectory->setText(QCoreApplication::translate("MainWindow", "Set data directory...", nullptr));
        actionLoadScenario->setText(QCoreApplication::translate("MainWindow", "Load scenario...", nullptr));
        menuFile->setTitle(QCoreApplication::translate("MainWindow", "Game", nullptr));
        menuData->setTitle(QCoreApplication::translate("MainWindow", "Data", nullptr));
        menuWindow->setTitle(QCoreApplication::translate("MainWindow", "Window", nullptr));
        variableView->setWindowTitle(QCoreApplication::translate("MainWindow", "Variables", nullptr));
        variableRemove->setText(QCoreApplication::translate("MainWindow", "-", nullptr));
        variableAdd->setText(QCoreApplication::translate("MainWindow", "+", nullptr));
        variableType->setPlaceholderText(QCoreApplication::translate("MainWindow", "Type (e.g. =u4)", nullptr));
        variableName->setPlaceholderText(QCoreApplication::translate("MainWindow", "New variable name", nullptr));
        scenarioView->setWindowTitle(QCoreApplication::translate("MainWindow", "Scenario information", nullptr));
        label_2->setText(QCoreApplication::translate("MainWindow", "Cumulative:", nullptr));
        label->setText(QCoreApplication::translate("MainWindow", "Reward:", nullptr));
        cumReward->setText(QCoreApplication::translate("MainWindow", "0", nullptr));
        resetScenario->setText(QCoreApplication::translate("MainWindow", "Reset scenario", nullptr));
        didEnd->setText(QCoreApplication::translate("MainWindow", "No", nullptr));
        reward->setText(QCoreApplication::translate("MainWindow", "0", nullptr));
        label_5->setText(QCoreApplication::translate("MainWindow", "Movie:", nullptr));
        movie->setText(QCoreApplication::translate("MainWindow", "None", nullptr));
        label_4->setText(QCoreApplication::translate("MainWindow", "Did end:", nullptr));
        label_3->setText(QCoreApplication::translate("MainWindow", "Done:", nullptr));
        done->setText(QCoreApplication::translate("MainWindow", "No", nullptr));
        label_6->setText(QCoreApplication::translate("MainWindow", "Frame:", nullptr));
        label_7->setText(QCoreApplication::translate("MainWindow", "Timestep:", nullptr));
        frame->setText(QCoreApplication::translate("MainWindow", "0", nullptr));
        ts->setText(QCoreApplication::translate("MainWindow", "0", nullptr));
        searchView->setWindowTitle(QCoreApplication::translate("MainWindow", "Search", nullptr));
        searchSubmit->setText(QCoreApplication::translate("MainWindow", "Search", nullptr));
        searchName->setPlaceholderText(QCoreApplication::translate("MainWindow", "Search name", nullptr));
        searchType->setItemText(0, QCoreApplication::translate("MainWindow", "Is", nullptr));
        searchType->setItemText(1, QCoreApplication::translate("MainWindow", "Increased by", nullptr));
        searchType->setItemText(2, QCoreApplication::translate("MainWindow", "Decreased by", nullptr));
        searchType->setItemText(3, QCoreApplication::translate("MainWindow", "Increased", nullptr));
        searchType->setItemText(4, QCoreApplication::translate("MainWindow", "Decreased", nullptr));
        searchType->setItemText(5, QCoreApplication::translate("MainWindow", "Changed", nullptr));
        searchType->setItemText(6, QCoreApplication::translate("MainWindow", "Unchanged", nullptr));

        searchRemove->setText(QCoreApplication::translate("MainWindow", "-", nullptr));
        searchMigrate->setText(QCoreApplication::translate("MainWindow", "Make variable", nullptr));
        cheatView->setWindowTitle(QCoreApplication::translate("MainWindow", "Cheats", nullptr));
        cheatName->setPlaceholderText(QCoreApplication::translate("MainWindow", "New cheat name", nullptr));
        cheatAdd->setText(QCoreApplication::translate("MainWindow", "+", nullptr));
        cheatRemove->setText(QCoreApplication::translate("MainWindow", "-", nullptr));
        cheatValue->setPlaceholderText(QString());
        (void)MainWindow;
    } // retranslateUi

};

namespace Ui {
    class MainWindow: public Ui_MainWindow {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_MAINWINDOW_H
