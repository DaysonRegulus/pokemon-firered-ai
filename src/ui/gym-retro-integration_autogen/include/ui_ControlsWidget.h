/********************************************************************************
** Form generated from reading UI file 'ControlsWidget.ui'
**
** Created by: Qt User Interface Compiler version 5.15.3
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_CONTROLSWIDGET_H
#define UI_CONTROLSWIDGET_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QDialog>
#include <QtWidgets/QDialogButtonBox>
#include <QtWidgets/QFormLayout>
#include <QtWidgets/QGroupBox>
#include <QtWidgets/QHBoxLayout>
#include <QtWidgets/QVBoxLayout>

QT_BEGIN_NAMESPACE

class Ui_ControlsWidget
{
public:
    QVBoxLayout *verticalLayout;
    QHBoxLayout *players;
    QGroupBox *platform;
    QFormLayout *formLayout;
    QDialogButtonBox *buttonBox;

    void setupUi(QDialog *ControlsWidget)
    {
        if (ControlsWidget->objectName().isEmpty())
            ControlsWidget->setObjectName(QString::fromUtf8("ControlsWidget"));
        ControlsWidget->resize(268, 203);
        verticalLayout = new QVBoxLayout(ControlsWidget);
        verticalLayout->setObjectName(QString::fromUtf8("verticalLayout"));
        players = new QHBoxLayout();
        players->setObjectName(QString::fromUtf8("players"));
        platform = new QGroupBox(ControlsWidget);
        platform->setObjectName(QString::fromUtf8("platform"));
        formLayout = new QFormLayout(platform);
        formLayout->setObjectName(QString::fromUtf8("formLayout"));

        players->addWidget(platform);


        verticalLayout->addLayout(players);

        buttonBox = new QDialogButtonBox(ControlsWidget);
        buttonBox->setObjectName(QString::fromUtf8("buttonBox"));
        buttonBox->setOrientation(Qt::Horizontal);
        buttonBox->setStandardButtons(QDialogButtonBox::Cancel|QDialogButtonBox::Save);

        verticalLayout->addWidget(buttonBox);


        retranslateUi(ControlsWidget);
        QObject::connect(buttonBox, SIGNAL(accepted()), ControlsWidget, SLOT(accept()));
        QObject::connect(buttonBox, SIGNAL(rejected()), ControlsWidget, SLOT(reject()));

        QMetaObject::connectSlotsByName(ControlsWidget);
    } // setupUi

    void retranslateUi(QDialog *ControlsWidget)
    {
        ControlsWidget->setWindowTitle(QCoreApplication::translate("ControlsWidget", "Controls", nullptr));
        platform->setTitle(QCoreApplication::translate("ControlsWidget", "platform", nullptr));
    } // retranslateUi

};

namespace Ui {
    class ControlsWidget: public Ui_ControlsWidget {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_CONTROLSWIDGET_H
